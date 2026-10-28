# Fast template production

## Generate a website

The AI chooses an available industry template with `python3 tools/quick_site.py templates`. Electrician is the first template: the base layout, generic English copy, English routes and reusable stock imagery. Personalization changes the business name, phone/email, address and one theme color only.

```sh
./website --template electrician --name "Bright Electrical" --theme-color "#2563eb" --phone "+44 20 7946 0958" --email "hello@business.com" --street "10 High Street" --city "London"
```

`--theme-color "#2563eb"` sets the business color. The AI selects this color from the business’s logo/brand, or uses a suitable industry fallback if no clear brand color exists. Do not ask the user to choose it. JSON input uses `theme_color`. The prepared site automatically derives light/dark shades and updates buttons, highlights, borders, logo graphics and animations. All business-specific values live in the generated `site/business.js`; changing that configuration and reloading updates the entire site without rebuilding. Keep generic copy, photographs, layout and services unchanged per business.

The AI collects the name, phone/email and address from the business website, records the source, chooses the color, and runs the command itself. Do not hand this command back to the user as the next step. Name and at least one contact method are required. Street, city and postcode (`--zip`) are optional. No hours, ratings, registration numbers or other unverified details are invented. The command validates inputs, creates an isolated unique directory, copies the prepared static build, and writes a safely encoded `business.js` file. It reports the output directory and measured generation time. Repeated names create separate sites and never overwrite previous sites. Generation uses no API, image search or npm subprocess.

For a JSON array of business objects with the same fields:

```sh
python3 tools/quick_site.py batch businesses.json
```

After the command succeeds, continue directly to verification, deployment and outreach under the run’s authorization. The dashboard shows generated previews automatically; it is not an input form for business details or color. Local previews remain available while the dashboard is serving. Generated sites live under `runs/quick/ID/site/`; their business and image-provenance manifests live alongside the site. For an outreach job, record the generated folder in the existing ledger and proceed through the existing stages truthfully.

## Prepare once after editing the template

Edit `templates/electrician/`, preserving the template's visual design. User-facing copy and URLs are English. Stock images are bundled locally and described as illustrative, never as the prospect’s team or work. Their source and licence information is in `stock-images.json`; the imagery guidance came from the upstream author's own `build-premium-website` skill (not included in this fork).

```sh
python3 tools/quick_site.py prepare --template electrician
```

This installs dependencies only if absent, lints, builds and fingerprints the source. Generation refuses a missing or stale prepared build. Do full desktop/mobile and route QA after master edits, then reuse that verified build across businesses. Do not rebuild per business. Keep the original Delivery template and existing customer runs intact.

## Verification and hosting boundary

Check generated name, phone and email. Confirm English copy, responsive layout and working service/contact navigation after template changes. Forms remain clearly labelled previews and send nothing. Keep noindex on speculative previews. These are static React previews; generating a copy does not prerender each route or create a customer lead backend. Do not claim those capabilities.

The approximately 30-second goal covers applying the collected details and creating a ready-to-host local site. Discovery, hosting latency, public verification and outreach take additional time. New template versions affect only future generated copies.

## Vercel

Use the CLI wrapper (`pnpm dlx vercel@59.16.0`) with the operator's scope from `sender.local.json` (`vercel_scope`, written `SCOPE` below); confirm it read-only with `whoami` and `teams ls` at runtime. Exact CLI behavior: [deploy](https://vercel.com/docs/cli/deploy), [global options](https://vercel.com/docs/cli/global-options). Firecrawl uses [v2 scrape](https://docs.firecrawl.dev/api-reference/endpoint/scrape).

Create a new project named `revamp-JOB_ID` from the exact `site` path returned by the generator (normally `runs/quick/GENERATED_ID/site`), with no copied `.vercel` folder or env variables. Link explicitly to that project and the configured scope using CLI help for installed syntax. For example, from the copy:

```sh
pnpm dlx vercel@59.16.0 link --yes --project revamp-JOB_ID --scope SCOPE
pnpm dlx vercel@59.16.0 deploy --prod --yes --scope SCOPE
```

`--prod` is acceptable for this isolated concept project so the recipient receives a public URL; it must never refer to the business's real site or Delivery's existing platform/agency/client projects. Verify `.vercel/project.json` refers to the intended new project before deploying. The quick generator already outputs a complete static site. Deploy that `site/` directory with no install or build command. Its `vercel.json` provides the SPA fallback and noindex headers. Verify that `.vercel/project.json` belongs to the intended new isolated project before any subsequent deploy. Never run npm in the generated site or use the legacy per-business prerender workflow.

Capture and verify the returned URL. Open the homepage and a service route without session bypass cookies. If deployment protection blocks recipients, flag it; do not change account-wide protection settings. Do not send an inaccessible URL. Only ready/verified sites proceed to outreach. Hosting pricing is not known from a successful deploy; never promise a particular price, free hosting or automatic ownership transfer.

## Continue through outreach

After verifying the public preview, render the draft with `tools/sender.py message` and hand it off with [manual outreach](manual-outreach.md); that completes the job in this fork's default drafts mode. Submission through `contact-begin`/`contact-finish` applies only when the operator has enabled `outreach.auto_submit` and asked for it (see [outreach](outreach.md)). A local preview alone does not complete a job, and never switch to email or SMS.
