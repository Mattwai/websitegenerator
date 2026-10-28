import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('pagespeed', ROOT / 'tools/pagespeed.py')
pagespeed = importlib.util.module_from_spec(spec); spec.loader.exec_module(pagespeed)

RESPONSE = {'lighthouseResult': {
    'finalUrl': 'https://business.example/',
    'categories': {'performance': {'score': 0.23}, 'accessibility': {'score': 0.71},
                   'best-practices': {'score': 0.5}, 'seo': {'score': 0.92}},
    'audits': {
        'viewport': {'title': 'Has a <meta name="viewport"> tag', 'score': 0},
        'is-on-https': {'title': 'Uses HTTPS', 'score': 1},
        'largest-contentful-paint': {'title': 'Largest Contentful Paint', 'score': 0.1, 'displayValue': '9.8 s'},
        'cumulative-layout-shift': {'title': 'Cumulative Layout Shift', 'score': 0.9, 'displayValue': '0.05'},
    }}}


class PageSpeedTests(unittest.TestCase):
    def test_summary_scores_and_findings(self):
        summary = pagespeed.summarize(RESPONSE, 'mobile')
        self.assertEqual(summary['scores'], {'performance': 23, 'accessibility': 71, 'best-practices': 50, 'seo': 92})
        self.assertEqual(summary['metrics']['largest-contentful-paint'], '9.8 s')
        findings = ' | '.join(summary['findings'])
        self.assertIn('Mobile performance score 23/100', findings)
        self.assertIn('viewport', findings)
        self.assertIn('9.8 s', findings)
        self.assertNotIn('HTTPS', findings)
        self.assertNotIn('seo', findings.lower())

    def test_missing_audits_and_categories_tolerated(self):
        summary = pagespeed.summarize({'lighthouseResult': {'categories': {}, 'audits': {}}}, 'desktop')
        self.assertEqual(summary['scores'], {})
        self.assertEqual(summary['findings'], [])

    def test_request_url_with_and_without_key(self):
        query = parse_qs(urlsplit(pagespeed.request_url('https://b.example/', 'mobile', 'K')).query)
        self.assertEqual(query['strategy'], ['mobile'])
        self.assertEqual(set(query['category']), {'PERFORMANCE', 'ACCESSIBILITY', 'BEST_PRACTICES', 'SEO'})
        self.assertEqual(query['key'], ['K'])
        self.assertNotIn('key', parse_qs(urlsplit(pagespeed.request_url('https://b.example/', 'mobile', None)).query))
        with self.assertRaises(ValueError): pagespeed.request_url('ftp://b.example/', 'mobile', None)

    def test_cli_writes_summary_only(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'pagespeed-mobile.json'
            with patch.object(pagespeed, 'get_json', return_value=RESPONSE), patch.dict('os.environ', {}, clear=True):
                self.assertEqual(pagespeed.main(['audit', '--url', 'https://business.example/', '--out', str(out)]), 0)
            saved = json.loads(out.read_text())
            self.assertEqual(saved['scores']['performance'], 23)
            self.assertNotIn('lighthouseResult', saved)


if __name__ == '__main__':
    unittest.main()
