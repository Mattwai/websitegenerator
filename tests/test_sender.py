import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('sender', ROOT / 'tools/sender.py')
sender = importlib.util.module_from_spec(spec); spec.loader.exec_module(sender)

VALID = {'name': 'Sam Operator', 'first_name': 'Sam', 'email': 'sam@operator.example',
         'phone': '+61 400 000 000', 'offer': 'The website is free; you only pay for hosting.'}


class SenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'sender.local.json'
    def tearDown(self):
        self.tmp.cleanup()
    def write(self, data):
        self.path.write_text(json.dumps(data)); return self.path

    def test_missing_file_explains_setup(self):
        with self.assertRaisesRegex(ValueError, 'sender.example.json'): sender.load(self.path)
    def test_required_fields_and_placeholders_rejected(self):
        for field in ('name', 'first_name', 'email', 'offer'):
            with self.assertRaisesRegex(ValueError, field):
                sender.load(self.write({k: v for k, v in VALID.items() if k != field}))
        with self.assertRaisesRegex(ValueError, 'placeholder'):
            sender.load(self.write({**VALID, 'phone': '<YOUR_PHONE>'}))
        with self.assertRaisesRegex(ValueError, 'email'):
            sender.load(self.write({**VALID, 'email': 'not-an-email'}))
    def test_message_identifies_sender_and_offers_opt_out(self):
        subject, body = sender.render(sender.load(self.write(VALID)), 'https://revamp-x.vercel.app', 'Bright Electrical')
        self.assertEqual(subject, 'I made a website preview for Bright Electrical')
        for expected in ('https://revamp-x.vercel.app', 'Sam Operator', 'sam@operator.example', '+61 400 000 000',
                         VALID['offer'], "won't contact you again"):
            self.assertIn(expected, body)
        self.assertNotIn('{', body)
    def test_phone_is_optional(self):
        _, body = sender.render(sender.load(self.write({k: v for k, v in VALID.items() if k != 'phone'})), 'https://p.example')
        self.assertIn('email me at sam@operator.example', body)
    def test_preview_must_be_https(self):
        with self.assertRaises(ValueError): sender.render(sender.load(self.write(VALID)), 'http://p.example')
    def test_cli_writes_once_and_refuses_overwrite(self):
        out = Path(self.tmp.name) / 'outreach.txt'
        cmd = [sys.executable, str(ROOT / 'tools/sender.py'), 'message', '--sender-file', str(self.write(VALID)),
               '--preview-url', 'https://p.example', '--business', 'Acme', '--out', str(out)]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        self.assertIn('https://p.example', out.read_text())
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
    def test_services_template_uses_vars_and_needs_no_preview(self):
        subject, body = sender.render(sender.load(self.write(VALID)), template='services', business='Bright Electrical',
                                      variables={'rating': '4.8', 'reviews': '212', 'mobile_score': '23',
                                                 'gap': 'there is no way to book online'})
        for expected in ('Bright Electrical', '212 reviews', '23/100', 'no way to book online', 'Sam Operator',
                         "won't contact you again"):
            self.assertIn(expected, body)
        self.assertNotIn('{', body)
        self.assertIn('Bright Electrical', subject)
    def test_offer_can_be_overridden_per_business(self):
        _, body = sender.render(sender.load(self.write(VALID)), template='services', business='B',
                                variables={'rating': '5', 'reviews': '9', 'mobile_score': '40', 'gap': 'x',
                                           'offer': 'A per-business offer.'})
        self.assertIn('A per-business offer.', body)
    def test_services_template_names_lighthouse_not_pagespeed(self):
        _, body = sender.render(sender.load(self.write(VALID)), template='services', business='B',
                                variables={'rating': '5', 'reviews': '9', 'mobile_score': '40', 'gap': 'x'})
        self.assertIn("Google's Lighthouse test", body)
    def test_missing_template_variable_is_named(self):
        with self.assertRaisesRegex(ValueError, 'mobile_score'):
            sender.render(sender.load(self.write(VALID)), template='services', business='B',
                          variables={'rating': '4.8', 'reviews': '2', 'gap': 'x'})
    def test_unknown_template_rejected(self):
        with self.assertRaisesRegex(ValueError, 'template'):
            sender.render(sender.load(self.write(VALID)), 'https://p.example', template='../../etc/passwd')
    def test_no_personal_details_tracked(self):
        settings = json.loads((ROOT / 'settings.json').read_text())
        self.assertNotIn('sender', settings)
        self.assertNotIn('vercel_scope', settings)
        self.assertIn('sender.local.json', (ROOT / '.gitignore').read_text())


if __name__ == '__main__':
    unittest.main()
