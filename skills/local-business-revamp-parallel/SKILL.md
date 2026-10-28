---
name: local-business-revamp-parallel
description: Run larger city- or state-wide local-business lead batches with one coordinator that owns the browser and Agent-tool subagents for screening, preview builds, deploys and drafting. Drafts only by default. Use for big batches of the local-business-revamp workflow, not for skill edits.
---

# Parallel local-business batches (Claude Code)

Resolve this file's real path (it may be a symlink). The application root is two directories above this skill folder: `cd` there and follow the main [SKILL.md](../../SKILL.md). Its preflight, drafts-by-default rule, qualification rules, untrusted-content rule and finish checks all apply. This file only adds how to split the work. Creating or editing this skill does not launch a batch.

## Scope

Get industry, location (city or state) and count (default 5). For a state, the coordinator finds its cities from an authoritative public list and records the source. Write `runs/scouting/BATCH_ID/scope.json`: scope type, state, country, target, city-list sources, and a city queue with ids, status and coverage paths. Only the coordinator writes it. The ledger's location field is called `city`, so store the state label there. One target covers the whole state, not one per city. Work larger cities first and don't declare a state exhausted because one city or query came up empty.

## Roles

**Coordinator (you).** Runs discovery with `tools/places.py` per city, which needs no browser, and records queries and result counts in `scope.json`. Also owns the Chrome DevTools MCP browser exclusively, because it's one shared Chrome and its page selection and viewport are global. You do every browser step in sequence:
- Fallback Google discovery from the configured start page, only when Places is unavailable.
- Ambiguous form checks and narrow-viewport checks, resetting emulation afterwards.
- Public-preview verification of each deployed site.

You also own the ledger writes `add`, `claim` and `alias`, dedupe across cities and batches (domain, aliases, phone, email, name and address), and `scope.json`.

**Subagents (`Agent` tool, `subagent_type: general-purpose`, `model` = `worker_model` from settings).** Never use the browser. Each assignment is self-contained because subagents start cold. It includes:
- The application root path.
- Role, batch ID, job ID and the exclusive worker ID used for `claim`.
- The evidence directory.
- This line: *"Drafts only: never submit a form, send email or SMS, or edit settings.json."*

Typical assignments:

1. **Screen**: run `tools/pagespeed.py audit` (mobile) and Firecrawl `site_assets.py scrape --screen` + `scout_screen.py` for a candidate, `Read` the saved screenshot, and return PageSpeed scores and findings, at least one visual finding of its own, observed service gaps (for a `services` offer), contact routes with sources, the brand color and a qualify/skip recommendation. Write results to `runs/scouting/BATCH_ID/CITY_ID/<domain>/`. No ledger writes.
2. **Build and deploy** (`website` offer only; a `services` job skips straight to drafting): for a claimed job, advance the ledger stages, run `./website …` with verified facts, record `workspace`, deploy `site/` to `revamp-JOB_ID` in the operator's `vercel_scope`, then return the preview URL. You verify it in the browser, set `preview_url` / `preview_verified`, and move it to `ready`.
3. **Draft**: for a `ready` job, run `tools/sender.py message` then `control.py manual-outreach` with the verified routes, and return the result.

Run independent assignments in parallel by sending several `Agent` calls in one message. Keep at most `requested_workers` from settings running at once, matched by `control.py capacity N`. The ledger's owner IDs are locks, not extra agents.

## Flow and stopping

Keep discovery a little ahead of building: at most two qualified candidates waiting beyond active builds. Completed plus in-progress jobs reserve target slots. Skipped, blocked and uncertain prospects need fresh replacements; never retry those identities. In drafts mode, count **manual** jobs toward the requested number (see coordination's *Drafts-only target*).

Stay in the loop until the target is drafted, discovery is documented as exhausted, the operator stops it, or a concrete blocker stops all remaining work. One skip, a finished subagent or a status question is not a stopping point. Before the final report, check that no subagent is still running, and reconcile `scope.json` with the ledger. Then report counts per city and in total: reviewed, hosted, drafted, skipped, blocked and uncertain, plus any shortfall.
