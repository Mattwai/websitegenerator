import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('places', ROOT / 'tools/places.py')
places = importlib.util.module_from_spec(spec); spec.loader.exec_module(places)
control = places.control


def place(n, website=True, status='OPERATIONAL', reviews=10, phone=None):
    item = {'id': f'P{n}', 'displayName': {'text': f'Business {n}'}, 'formattedAddress': f'{n} Main St, Geelong VIC',
            'businessStatus': status, 'rating': 4.5, 'userRatingCount': reviews,
            'googleMapsUri': f'https://maps.google.com/?cid={n}', 'types': ['electrician']}
    if website: item['websiteUri'] = f'https://www.business{n}.example/'
    if phone: item['internationalPhoneNumber'] = phone
    return item


class PlacesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = control.DB; control.DB = Path(self.tmp.name) / 'ledger.db'
    def tearDown(self):
        control.DB = self.old_db; self.tmp.cleanup()

    def test_paginates_with_field_mask_and_stops_at_max_pages(self):
        pages = [{'places': [place(1)], 'nextPageToken': 'T1'}, {'places': [place(2)], 'nextPageToken': 'T2'},
                 {'places': [place(3)]}]
        with patch.object(places, 'post_json', side_effect=pages) as http:
            found = places.search('electricians in Geelong', key='K', max_pages=2, region='au')
        self.assertEqual([p['place_id'] for p in found], ['P1', 'P2'])
        self.assertEqual(http.call_count, 2)
        url, body, headers = http.call_args_list[1].args
        self.assertEqual(url, places.ENDPOINT)
        self.assertEqual(body['pageToken'], 'T1')
        self.assertEqual(body['regionCode'], 'au')
        self.assertEqual(headers['X-Goog-Api-Key'], 'K')
        for field in ('places.websiteUri', 'places.userRatingCount', 'places.rating', 'nextPageToken'):
            self.assertIn(field, headers['X-Goog-FieldMask'])

    def test_triage_splits_skips_dedupes_and_sorts_by_reviews(self):
        bid = control.batch('Electricians', 'Geelong')['id']
        control.add(bid, 'Known', 'https://business4.example', ['phone:+61355550100'])
        found = [places.normalize(p) for p in (
            place(1, reviews=5), place(2, reviews=120), place(3, website=False),
            place(5, status='CLOSED_PERMANENTLY'), place(4), place(6, phone='+61 3 5555 0100'))]
        report = places.triage(found)
        self.assertEqual([c['place_id'] for c in report['candidates']], ['P2', 'P1'])
        self.assertEqual([c['place_id'] for c in report['no_website']], ['P3'])
        reasons = {s['place_id']: s['reason'] for s in report['skipped']}
        self.assertIn('closed', reasons['P5'])
        self.assertIn('ledger', reasons['P4'])
        self.assertIn('ledger', reasons['P6'])

    def test_missing_key_is_explained(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'GOOGLE_MAPS_API_KEY'):
                places.keys.read_key('GOOGLE_MAPS_API_KEY', None)

    def test_cli_writes_report_without_storing_key(self):
        out = Path(self.tmp.name) / 'places.json'
        with patch.object(places, 'post_json', return_value={'places': [place(1)]}), \
             patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': 'SECRETKEY'}):
            self.assertEqual(places.main(['search', '--query', 'electricians in Geelong', '--out', str(out)]), 0)
        text = out.read_text()
        self.assertNotIn('SECRETKEY', text)
        self.assertEqual(json.loads(text)['candidates'][0]['website'], 'https://www.business1.example/')


if __name__ == '__main__':
    unittest.main()
