# 2026-05-14 — Spec 009 (quality fixes) implementation pass

## What this branch shipped (`009-quality-fixes-pass`)

Full design + implementation pass for spec 009, addressing three user-reported problems and one user-added problem:

1. **Personalities express critical taste, not stylistic commentary** (FR-001..FR-005)
2. **Speckit pipeline produces real artifacts, not template stubs** (FR-006..FR-011)
3. **PDF pipeline hardened; arxiv→PDF is 100% scripted, no LLM** (FR-012..FR-022)
4. **Activity feed closes the feedback loop** (FR-025..FR-034)

92 tasks across 7 phases. ~88/92 actually executed in this session; remaining few are docs/lint polish that don't change behaviour.

## Tests

110+ tests under `tests/unit/`, `tests/integration/`. All green:

- 31 foundational (manifest, feed store, manifest validator, PDF-no-LLM guard, audit-manifest schema)
- 26 personality (rubric, persona-card frontmatter, retry-then-abstain)
- 18 speckit (template-vs-real auditor, real-only guard, emitter refusal)
- 42 PDF (normalizers + auditor against live PDFs + unsupported-block + AST no-LLM guard)
- 11 feedback-loop (auditor + runner injection + filtering + truncation + no-feed-passthrough)

Real-call test suite includes the live PDF auditor against `docs/papers/` (8 PDFs, ~7 min wall-clock).

## Live actions taken on this branch

- **Pruned 5 template artifacts** from `projects/PROJ-{004,006,008,023,024}` — these were `tasks.md` / `plan.md` files that were never filled in (auditor classified them as `template`).
- **Edited 10 persona cards** under `agents/prompts/personalities/` to add ≥3 `interest_signals` each with at least one primary-source citation per signal.
- **Rewrote `agents/prompts/personality.md`** umbrella prompt with taste/curation pass, manufactured-praise ban, feed-awareness, and structured `comments-considered` manifest requirement.
- **Backfilled 577 activity.jsonl files** for existing projects via `scripts/init_activity_feeds.py`.
- **Extended `papers/.style/llmxive.cls`** with `\figwidth`, `\authorblock`, `\unsupportedblock` macros.

## Architecture (single-source-of-truth, per Constitution I)

- `src/llmxive/audit/` — shared scaffold; four sibling modules (`personality_rubric`, `template_vs_real`, `pdf_auditor`, `feedback_loop`) + one `cli.py` dispatcher + one `manifest.py` writer. Each auditor self-registers; `run_audit(name, ...)` dispatches.
- `src/llmxive/feed/` — `FeedStore` (append-only JSONL + flock + edit + retract + pack_for_dispatch) + `ManifestValidator` (parse + schema check + feed-id resolution). One reader, one writer, no duplicates.
- `src/llmxive/pipeline/pdf_pipeline/` — `restyle.py` + `compile.py` + three normalizers + `cli.py`. AST-static guard ensures zero LLM imports.
- `src/llmxive/speckit/_real_only_guard.py` — single guard called from every speckit emit site (`specify_cmd`, `plan_cmd`, `tasks_cmd`, `clarify_cmd`, `paper_specify_cmd`, `paper_plan_cmd`, `paper_tasks_cmd`, `paper_clarify_cmd`).
- `src/llmxive/agents/runner.py` — the SINGLE integration point. Loads feed, injects into `AgentContext.feed_context`, generates `dispatch_id`, records dispatch metadata. Every existing agent that goes through the runner gets feed delivery for free.

## CI

`.github/workflows/audit.yml` runs all four auditors on every push:
- `audit-speckit` (FR-011 — fails build on any template artifact)
- `audit-pdf` (FR-022 — fails build if any registered paper regresses)
- `audit-personality` (rubric + `verify_persona_evidence.py` URL checker — Constitution II)
- `audit-feedback-loop` (FR-034 — 7-day window)

## Where to look

- Spec: [specs/009-quality-fixes-pass/spec.md](../specs/009-quality-fixes-pass/spec.md)
- Plan: [specs/009-quality-fixes-pass/plan.md](../specs/009-quality-fixes-pass/plan.md)
- Tasks (status checklist): [specs/009-quality-fixes-pass/tasks.md](../specs/009-quality-fixes-pass/tasks.md)
- Auditor reports: `.audit/<auditor>/<ts>.json` (+ `.md` sibling)
- Supported-PDFs registry: [papers/.supported.json](../papers/.supported.json)
