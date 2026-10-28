#!/usr/bin/env python3
"""Score a business website with Lighthouse through the PageSpeed Insights API.

Usage: python3 tools/pagespeed.py audit --url https://business.example/ --out runs/scouting/BATCH_ID/cache/DOMAIN/pagespeed-mobile.json

Runs on Google's side, so it needs no local browser and can run in parallel. Saves a compact summary
(0-100 category scores, key metrics, plain-English findings), not the multi-megabyte raw report.
GOOGLE_MAPS_API_KEY (with the PageSpeed Insights API enabled) raises the quota; without it the
anonymous quota applies.
"""
import argparse
import json
from pathlib import Path
import sys
import urllib.request
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keys  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'
CATEGORIES = ('PERFORMANCE', 'ACCESSIBILITY', 'BEST_PRACTICES', 'SEO')
METRICS = ('largest-contentful-paint', 'cumulative-layout-shift', 'total-blocking-time', 'speed-index')
FAILING_AUDITS = {'viewport': 'No mobile viewport tag: the page is not set up for phones',
                  'is-on-https': 'Not served over HTTPS',
                  'font-size': 'Text too small to read on a phone',
                  'tap-targets': 'Buttons and links too small or close together to tap',
                  'image-aspect-ratio': 'Images are stretched or squashed',
                  'errors-in-console': 'Page throws errors in the browser'}


def request_url(url, strategy, key):
    if urlsplit(url).scheme not in ('http', 'https'):
        raise ValueError('Audit a public http(s) URL')
    params = [('url', url), ('strategy', strategy)] + [('category', c) for c in CATEGORIES]
    if key: params.append(('key', key))
    return ENDPOINT + '?' + urlencode(params)


def get_json(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read(30_000_001))


def summarize(response, strategy):
    result = response.get('lighthouseResult', {})
    scores = {name: round(cat['score'] * 100) for name, cat in result.get('categories', {}).items()
              if isinstance(cat, dict) and isinstance(cat.get('score'), (int, float))}
    audits = result.get('audits', {})
    metrics = {m: audits[m].get('displayValue') for m in METRICS if m in audits and audits[m].get('displayValue')}
    findings = []
    label = strategy.capitalize()
    for name in ('performance', 'accessibility'):
        if name in scores and scores[name] < 50:
            findings.append(f'{label} {name} score {scores[name]}/100 (Google Lighthouse)')
    lcp = audits.get('largest-contentful-paint', {})
    if isinstance(lcp.get('score'), (int, float)) and lcp['score'] < 0.5 and lcp.get('displayValue'):
        findings.append(f"Main content takes {lcp['displayValue']} to appear on {strategy}")
    for audit, text in FAILING_AUDITS.items():
        score = audits.get(audit, {}).get('score')
        if isinstance(score, (int, float)) and score < 0.5:
            findings.append(f'{text} ({audit})')
    return {'url': result.get('finalUrl', ''), 'strategy': strategy, 'scores': scores,
            'metrics': metrics, 'findings': findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('audit')
    a.add_argument('--url', required=True)
    a.add_argument('--out', type=Path, required=True)
    a.add_argument('--strategy', choices=('mobile', 'desktop'), default='mobile')
    a.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args(argv)
    try:
        key = keys.read_key('GOOGLE_MAPS_API_KEY', args.env_file, required=False)
        summary = summarize(get_json(request_url(args.url, args.strategy, key)), args.strategy)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'out': str(args.out), 'scores': summary['scores'], 'findings': summary['findings']}))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
