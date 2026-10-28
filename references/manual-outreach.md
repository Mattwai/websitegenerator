# Manual outreach after website completion

**This is the default route in this fork:** with `outreach.auto_submit` false, every qualified business ends here. It also applies whenever automatic outreach is unavailable: no contact form, email-only contact, a visible CAPTCHA, an unsuitable newsletter/review form, or a form that cannot be filled without unsupported commitments. Do not solve CAPTCHA or make commitments. Record `outreach_mode: manual` in supported job fields with the reason in qualification evidence, then continue normal generation, QA, deployment and public verification. Collect publicly verified email/phone, the contact form URL if any, and source URLs for the operator. Do not invent unavailable contact details. Put the best route in the `--reason`.

This changes contact eligibility, not business qualification. Duplicates, previously contacted businesses, opt-outs/no-solicitation, visually strong sites and out-of-scope businesses remain skipped. Deployment/QA failures remain blocked until resolved. Manual is not an alternative route around an actual approval rejection; follow the applicable rule and surface required human action. Ambiguous prior submissions remain uncertain, never a prompt to send again.

After a verified public website reaches `ready`, render the draft with `python3 tools/sender.py message --preview-url … --business … --out runs/JOB_ID/outreach.txt`. For a `services` job (`offer_kind: services`), no site is built: once the job is qualified (stage `extracting` with reason, two findings, sources and screenshots), render with `--template services` (see [outreach](outreach.md)) and hand off directly. The ledger allows this only for `services` jobs. Then:

```sh
python3 tools/control.py manual-outreach --job JOB_ID --worker WORKER_ID --reason 'No usable original contact form; please send the prepared proposal manually.' --message-file runs/JOB_ID/outreach.txt --email 'verified@business.example' --phone '+16175550123'
```

Use verified values; omit unavailable `--email` or `--phone`. `source_urls` must already contain the evidence for those details. The command verifies readiness, saves `data.manual_outreach` (reason, exact message, email, phone, sources), sets stage `manual` and contact status `manual_required`, and releases worker capacity. The dashboard shows Manual outreach, the verified preview, contact details and a copyable message. It sends no email or other message automatically.

Do not use generic `update --stage manual`: the dedicated command enforces evidence requirements. Do not reserve `contact-begin` for a manual job. A job with a reserved/attempted submission cannot automatically become manual; preserve its history and record submitted/uncertain/blocked according to the observed action. In particular, do not send again after an ambiguous result.

Manual means the website is ready and the operator still needs to send outreach. It is terminal for agent processing, is displayed/countable separately, and does not count as a completed send under the existing batch target rule. Keep its identity reserved across future batches. Do not automatically recover it or generate another site for that business. Continue discovery toward the completed-send target while reporting the manual backlog separately.

Apply this to newly processed qualified prospects. Do not silently relabel historical skips as manual: they may lack a generated/verified site or reflect an opt-out. Historical prospects require explicit reprocessing and actual QA/deployment before entering manual.
