#!/usr/bin/env python3
"""Discover local-business candidates with Google Places API (New) Text Search.

Usage: python3 tools/places.py search --query 'electricians in Geelong VIC' --out runs/scouting/BATCH_ID/places-geelong.json

Seeds discovery only: every fact that goes into the ledger or an outreach draft is re-verified on the
business's own website. Candidates are sorted by review count (a demand signal) and checked against the
ledger so known businesses are not proposed again. Requires GOOGLE_MAPS_API_KEY (Places API (New) enabled).
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import control  # noqa: E402
import keys  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://places.googleapis.com/v1/places:searchText'
FIELDS = ('places.id', 'places.displayName', 'places.formattedAddress', 'places.websiteUri',
          'places.internationalPhoneNumber', 'places.rating', 'places.userRatingCount',
          'places.businessStatus', 'places.googleMapsUri', 'places.types', 'nextPageToken')


def post_json(url, body, headers):
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                     headers={'Content-Type': 'application/json', **headers})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read(5_000_001))


def normalize(raw):
    return {'place_id': raw.get('id'), 'name': (raw.get('displayName') or {}).get('text', ''),
            'address': raw.get('formattedAddress', ''), 'website': raw.get('websiteUri', ''),
            'phone': raw.get('internationalPhoneNumber', ''), 'rating': raw.get('rating'),
            'reviews': raw.get('userRatingCount') or 0, 'status': raw.get('businessStatus', ''),
            'maps_url': raw.get('googleMapsUri', ''), 'types': raw.get('types', [])}


def search(query, key, max_pages=3, region=None):
    headers = {'X-Goog-Api-Key': key, 'X-Goog-FieldMask': ','.join(FIELDS)}
    found, token = [], None
    for _ in range(max(1, min(max_pages, 3))):
        body = {'textQuery': query, 'pageSize': 20}
        if region: body['regionCode'] = region
        if token: body['pageToken'] = token
        page = post_json(ENDPOINT, body, headers)
        found.extend(normalize(p) for p in page.get('places', []))
        token = page.get('nextPageToken')
        if not token:
            break
    return found


def ledger_match(c, candidate):
    probes = []
    if candidate['website']:
        try: probes.append('domain:' + control.domain(candidate['website']))
        except ValueError: pass
    if candidate['phone']:
        try: probes.append(control.identity('phone:' + candidate['phone']))
        except ValueError: pass
    for probe in probes:
        row = c.execute('SELECT job_id FROM identities WHERE identity=?', (probe,)).fetchone()
        if row: return row['job_id']
    return None


def triage(found):
    candidates, no_website, skipped = [], [], []
    with control.connect() as c:
        for item in found:
            if item['status'] and item['status'] != 'OPERATIONAL':
                skipped.append({**item, 'reason': f"closed or not operational ({item['status']})"}); continue
            job = ledger_match(c, item)
            if job:
                skipped.append({**item, 'reason': f'already in ledger as {job}'}); continue
            (candidates if item['website'] else no_website).append(item)
    def by_reviews(group): return sorted(group, key=lambda x: -x['reviews'])
    return {'candidates': by_reviews(candidates), 'no_website': by_reviews(no_website), 'skipped': skipped}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('search')
    s.add_argument('--query', required=True)
    s.add_argument('--out', type=Path, required=True)
    s.add_argument('--max-pages', type=int, default=3, help='1-3 pages of 20 results')
    s.add_argument('--region', help='CLDR region code to bias results, e.g. au')
    s.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args(argv)
    try:
        found = search(args.query, keys.read_key('GOOGLE_MAPS_API_KEY', args.env_file), args.max_pages, args.region)
        report = {'query': args.query, 'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                  'note': 'Discovery seed only; verify every fact on the business website before using it.',
                  **triage(found)}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps({'out': str(args.out), 'candidates': len(report['candidates']),
                          'no_website': len(report['no_website']), 'skipped': len(report['skipped'])}))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
