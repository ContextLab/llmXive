# Reviewed Preprints — design spec

**Date:** 2026-07-01
**Status:** APPROVED (2026-07-01) — user confirmed §4 (prepend title page) + §5
(credit underlying model) + §7 (dry-run migration); proceeding to implementation.
**Author:** llmXive maintainer + Claude

## Problem / motivation

Externally-ingested papers (arXiv scrape, HuggingFace papers, user submissions —
177 currently, spread across every pipeline stage) keep the **original paper's
author set** (`paper/metadata.json::authors`). The current reprocess pipeline
(`paper_reprocess/`) routes code-bearing intakes through `branch_code`, which
**backfills specs and revises the paper** — i.e. llmXive *modifies* the paper and
then presents the modified work in the "Published" tab with the original authors
still credited, **without those authors' consent**. That is an ethics violation:
we have no consent to modify a third party's work and attribute the result to them.

## Principle (the invariant, enforced in code)

**An ingested paper's body is never modified, and its original authors are never
presented as authors of any llmXive-modified artifact.** Each ingested paper
yields exactly two things:

1. A **terminal Reviewed Preprint** record — review-only, original work preserved.
2. A **separate, fresh llmXive brainstorm project** (the follow-up) — our own
   research, which *drops* the original byline and *cites* the original.

## User decisions (confirmed)

- **Structure:** two separate projects (preprint record vs. follow-up project).
- **Migration:** revert all 177 intake projects to review-only; discard llmXive
  modifications; preserve original paper + metadata.
- **Review scope:** run the full 7-reviewer panel ONCE (no convergence/revise, no
  accept/reject) → verdicts + consolidated action items.

## Design

### 1. New terminal stage + routing
- Add `Stage.REVIEWED_PREPRINT` (terminal — never advances).
- `graph.py` `PAPER_INGESTED` handler no longer calls `classify_paper` /
  `branch_code` / in-place `branch_nocode`. Instead it:
  1. runs the review-only pipeline (§3) → project lands at `REVIEWED_PREPRINT`;
  2. spawns a **new** `brainstormed` project (new PROJ id) via a refactored
     follow-up builder derived from `branch_nocode` (summarize → extract →
     propose extension), which drops the original byline and appends a bibtex
     cite to the source.
- `branch_code` is retired from the intake path (kept only if some other flow
  needs it; otherwise deleted per SSoT). `classify_paper` no longer gates
  modification.

### 2. Reviewed Preprint record (data)
- The ingested project stays at its own PROJ id, `current_stage =
  REVIEWED_PREPRINT`, retaining `paper/source`, `paper/pdf` (original),
  `paper/metadata.json` (original authors intact).
- New artifacts written under `paper/`: `paper/reviews/*` (panel records),
  `paper/action_items.md` (consolidated), `paper/pdf/original-llmxive.pdf`
  (themed original, §4), `paper/pdf/peer-review-llmxive.pdf` (review report, §4).
- A small `paper/preprint.json` marks it: `{is_reviewed_preprint: true,
  source_url, ingested_via, ingested_at, submitter}` — drives the UI + attribution.

### 3. Review-only pipeline
- Reuse the existing panel (`convergence/project_runner.py` / `engine.py` /
  `agents/research_reviewer.py`) to run the 7 reviewers ONCE on the preprint.
- Emit verdicts + a consolidated action-item list from the reviewers' concerns.
- **No convergence loop, no revise, no accept/reject** — a preprint is not ours
  to accept. The panel output is peer-review *feedback* only. The
  fabrication/marker/spec-quality backstops that normally gate advancement are
  NOT applied (nothing advances).

### 4. Theming (CONFIRMED — prepend a title page, never re-theme the body)
- **Original paper → `original-llmxive.pdf`:** PREPEND a single llmXive-themed
  title/info page to the ORIGINAL PDF (render the cover with `llmxive.cls`, then
  concatenate cover + original PDF pages via `pypdf`). The original PDF pages are
  untouched — no re-theme, no re-render, byte-preserved. The cover page lists:
  title, authors, abstract; a source/ingestion note (e.g. "Scraped from HuggingFace
  papers / submitted by <submitter> on <date>"); a brief llmXive explanation + link
  (https://github.com/ContextLab/llmXive); a link to the peer-review report; a link
  to the spawned follow-up llmXive project. (We currently re-theme the WHOLE PDF —
  that path is retired for intake papers; we only prepend.)
- **Review report → `peer-review-llmxive.pdf`:** the reviewer verdicts + feedback
  + action items laid out as a second `llmxive.cls`-themed PDF ("llmXive Peer
  Review of <title>").
- Reuse `pipeline/pdf_pipeline/restyle.py` + `papers/.style/llmxive.cls` to render
  the themed pages; `pypdf` to prepend the cover to the untouched original.

### 5. Attribution (the credit rule)
- `web_data._project_authors` gets a preprint-aware branch keyed on
  `preprint.json::is_reviewed_preprint`:
  - credit **only** (1) original authors (`metadata.json::authors`, role
    `paper_author`), (2) the submitter, (3) the **underlying model** that ran the
    review prompts — the run-log `model_name` (e.g. `claude-sonnet-4.7`), NOT the
    prompt/agent name — for runs whose agent role matches `*_reviewer_*`;
  - **exclude** implementer / reviser / backfill / planner roles (there are none,
    since we never modify — but the filter makes the invariant explicit and
    protects against regressions).
- The follow-up project uses the normal rules (llmXive models; original authors
  dropped via `_drop_original_authors`; cites the source).

### 6. Web UI — "Reviewed Preprints" tab
- New tab in `web/index.html` (`data-tab="reviewedPreprints"`) beside
  Published / In Progress / Activity / Contributors, with a count.
- `web/data/projects.json` grows a `reviewed_preprints` collection (built by
  `web_data.py` from `preprint.json`), each carrying: title, source_url,
  ingested_via, submitter, ingested_at, authors (original), review_models,
  action_items, and the two PDF paths.
- `app.js`: a preprint card variant + modal showing:
  - a **"Based on a preprint"** badge and a **link to the original source**;
  - an **ingestion statement** built from metadata (e.g. *"Ingested by llmXive
    on <date> — scraped from arXiv; submitted via <submitted_via> by
    <submitter>."*);
  - the **credit list** (original authors + submitter + review models, labeled);
  - in the modal: the themed original PDF, the peer-review report PDF, and the
    action-item list; a link to the spawned follow-up project.
- The follow-up projects appear normally in In Progress → Published, each citing
  its source preprint.

### 7. Migration of the 177 (CONFIRMED — dry-run first, spawn all follow-ups)
- One-time, auditable batch script (`scripts/migrate_reviewed_preprints.py`):
  - **Dry-run first** — emits a report: each intake PROJ, its current stage, what
    modifications would be discarded (backfilled specs/plan/tasks, in_progress
    code, any revised paper), the follow-up it would spawn. **You review before
    it executes.**
  - On execute: revert each to a clean Reviewed Preprint (discard llmXive
    modifications; preserve `paper/source`, original `paper/pdf`,
    `metadata.json`), run the review-only pipeline, write `preprint.json`, spawn
    the follow-up brainstorm.
- ⚑ RECOMMENDED: spawn all follow-ups, but the dry-run lets you approve first.
  ~177 new brainstorms is a lot of pipeline load; alternative: gate/stage the
  follow-ups (spawn on a schedule or on demand) rather than all at once.
  *Awaiting confirmation.*

## Reused components (SSoT — modify in place, no duplication)
- Follow-up: `paper_reprocess/branch_nocode.py` → refactor `to_followup_idea`
  into a "spawn separate follow-up project" builder.
- Theming: `pipeline/pdf_pipeline/restyle.py`, `papers/.style/llmxive.cls`,
  `normalize_authors.py`.
- Review: `convergence/project_runner.py`, `engine.py`,
  `agents/research_reviewer.py`.
- Attribution: `web_data.py::_project_authors`.
- Routing: `paper_reprocess/reprocess.py`, `pipeline/graph.py` PAPER_INGESTED.
- UI: `web/index.html`, `web/js/app.js`, `web/js/data.js`.

## Testing (real, no mocks — Constitution III)
- Unit: `preprint.json` gating of `_project_authors` (original authors + submitter
  + review-models only; implementer roles excluded); routing produces a terminal
  preprint + a separate brainstorm follow-up; follow-up drops byline + cites source.
- Real-call: run the review panel once on a real ingested paper; build both themed
  PDFs and open them to verify (title page/provenance present, body unchanged for
  the original).
- Migration: dry-run on the real 177; execute on a copy/subset first; verify no
  original paper bytes changed.
- UI: build `projects.json`, render the new tab, screenshot card + modal.

## Out of scope
- Changing how brainstorm-origin (non-intake) projects are handled.
- Re-litigating the review panel internals.

## Resolved decisions (2026-07-01)
1. §4: PREPEND a single llmXive title/info page; original PDF body untouched (no
   re-theme). Cover lists title/authors/abstract + source note + llmXive blurb+link
   + link to reviews + link to follow-up.
2. §5: review credit → the UNDERLYING model (run-log `model_name`, e.g.
   `claude-sonnet-4.7`), not the prompt/agent name.
3. §7: dry-run report first (maintainer eyeballs), then execute all 177 + spawn all
   follow-ups.
