# Outreach: drafts by default, one submit attempt only if enabled

## The message

The message is `references/outreach-template.txt`, rendered with the operator's details from the gitignored `sender.local.json`:

```sh
python3 tools/sender.py message --preview-url 'https://VERIFIED-PREVIEW' --business 'Business Name' --out runs/JOB_ID/outreach.txt
```

Use only a verified public `https://` preview URL. `sender.py` refuses to overwrite an existing draft. Don't hand-edit the rendered draft to add observed issues, "I checked your website", SEO claims or custom praise: visual findings stay internal evidence. Keep the sender identification and the opt-out line. Change the template wording only when the operator asks. Don't mimic a customer requesting service.

## Default: hand the draft to the operator

With `settings.json` `outreach.auto_submit` false (the shipped default), every qualified, verified job ends with `manual-outreach` (see [manual outreach](manual-outreach.md)). The dashboard shows the draft, the preview and the verified routes: contact form URL, email, phone. The operator sends it. Never send email or SMS yourself, and never submit a form.

## Only if the operator has enabled `auto_submit`

`contact-begin` refuses unless the flag is true. Even with the flag on, submit only when the current request explicitly asks for submission. Then:

1. Inspect the original contact page in the browser. Prefer a general enquiry form. Respect any visible no-solicitation notice by skipping and recording the opt-out. Don't use inspection/booking/quote forms for a sales message, and don't fabricate a problem, book a service or make commitments. Those prospects go to manual outreach.
2. Fill sender fields **only from `sender.local.json`** (`name`, or `first_name` and the rest of `name` split for surname fields; `email`; `phone` if present). If a form requires the business's own address, use its verified public address and record the source. Never present it as the sender's. Leave CAPTCHA challenges untouched and route the business to manual outreach. Don't tick newsletter or marketing-consent boxes.
3. Paste the rendered `runs/JOB_ID/outreach.txt` exactly. Check the filled values before reserving.
4. Reserve immediately before submitting. If the reservation fails, do not submit:

```sh
python3 tools/control.py contact-begin --job JOB_ID --worker WORKER_ID --message-file runs/JOB_ID/outreach.txt --form-url 'https://business.example/contact'
```

5. Click Submit **once**, then record what you actually observed:

```sh
python3 tools/control.py contact-finish --job JOB_ID --worker WORKER_ID --status submitted --evidence 'Clicked Submit once; observed: …; screenshot: …'
```

Use `blocked` when it is certain no submit happened after reservation, and `uncertain` when you can't tell. Never resend a completed or ambiguous attempt, and never switch to email or SMS as a fallback.
