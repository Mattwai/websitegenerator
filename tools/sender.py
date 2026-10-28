#!/usr/bin/env python3
"""Load the operator's sender details from a gitignored file and render the outreach draft.

Usage:
  python3 tools/sender.py check
  python3 tools/sender.py message --preview-url URL [--business NAME] --out runs/JOB_ID/outreach.txt

Personal details never live in tracked files: copy sender.example.json to sender.local.json.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SENDER_FILE = ROOT / 'sender.local.json'
TEMPLATE = ROOT / 'references' / 'outreach-template.txt'
REQUIRED = ('name', 'first_name', 'email', 'offer')
OPTIONAL = ('phone', 'business_name', 'vercel_scope')
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
PLACEHOLDER = re.compile(r'<[^>]*>|\bYOUR_|example\.com\b', re.I)


def load(path=SENDER_FILE):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'{path.name} not found: copy sender.example.json to {path.name} and fill it in')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'{path.name} must be a JSON object')
    for field in REQUIRED:
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f'{path.name}: "{field}" is required')
    for field, value in data.items():
        if field in REQUIRED + OPTIONAL and isinstance(value, str) and PLACEHOLDER.search(value):
            raise ValueError(f'{path.name}: "{field}" still holds a placeholder value')
    if not EMAIL.fullmatch(data['email'].strip()):
        raise ValueError(f'{path.name}: "email" is not a valid email address')
    return {k: data[k].strip() for k in REQUIRED + OPTIONAL if isinstance(data.get(k), str) and data[k].strip()}


def render(sender, preview_url, business=''):
    if not preview_url.startswith('https://'):
        raise ValueError('The preview URL must be a verified public https:// URL')
    if sender.get('phone'):
        contact_line = f"text me on {sender['phone']} or email {sender['email']}"
    else:
        contact_line = f"email me at {sender['email']}"
    signature = sender['name'] + (f", {sender['business_name']}" if sender.get('business_name') else '')
    body = TEMPLATE.read_text(encoding='utf-8').format(
        preview_url=preview_url, offer=sender['offer'], contact_line=contact_line,
        first_name=sender['first_name'], signature=signature)
    subject = f'I made a website preview for {business}' if business else 'I made a website preview for you'
    return subject, body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sender-file', type=Path, default=SENDER_FILE)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('check')
    m = sub.add_parser('message')
    m.add_argument('--sender-file', type=Path, default=argparse.SUPPRESS)
    m.add_argument('--preview-url', required=True)
    m.add_argument('--business', default='')
    m.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        sender = load(args.sender_file)
        if args.cmd == 'check':
            print(json.dumps({'ok': True, 'fields': sorted(sender)}, indent=2))
            return 0
        if args.out.exists():
            raise ValueError(f'Refusing to overwrite {args.out}; outreach drafts are written once')
        subject, body = render(sender, args.preview_url, args.business)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding='utf-8')
        print(json.dumps({'subject': subject, 'message_file': str(args.out)}, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
