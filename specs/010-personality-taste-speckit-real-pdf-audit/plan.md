# Implementation Plan: Personality Taste, Real Speckit Artifacts, PDF Audit

**Branch**: `feature/personalities-speckit-real-pdf-audit` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-personality-taste-speckit-real-pdf-audit/spec.md`

## Summary

Three independent thrusts addressing user-reported gaps in the live pipeline:

1. **Personality taste** — extend the deterministic rubric with three new required axes (explicit `position` in YAML frontmatter, liveness-checked adjacent-work pointer, named `interest_signal` anchor). Update the personality prompt template and persona cards' frontmatter contract; bias the rotation toward differential positions when a project has accumulated same-position contributions.

2. **Real speckit artifacts** — audit every speckit `.md` under `projects/**/specs/**/` and `projects/**/.specify/**/` using `llmxive.speckit._real_only_guard.is_real()`; delete templates transitively (downstream-from-template too); roll project stages back to the latest stage with surviving real artifacts; add a `PIPELINE_PARALLELISM=8` cap to the scheduler so the queue drains.

3. **PDF audit** — add a deterministic `llmxive pdf-pipeline audit` command that renders every page of every PDF under `docs/papers/PROJ-*/*.pdf` to PNG, runs a deterministic checker for known failure patterns (literal LaTeX commands, mixed cite glyphs, off-spec figure widths, non-canonical author blocks, section-number gaps), classifies failures (source-fixable / unsupported-construct / source-missing), quarantines tool crashes, and drives `docs/papers/` to zero failing pages. Zero LLM calls — enforced by the existing AST test (`tests/unit/test_pdf_pipeline_no_llm.py`).

## Technical Context

**Language/Version**: Python 3.11 (project standard; `pyproject.toml` pins `>=3.11`)
**Primary Dependencies**:
- Existing: `pydantic`, `pyyaml`, `click`, `requests` (HTTP for liveness), `pdfminer.six` (PDF text extraction in existing pipeline), `pillow` (PNG handling).
- New: `pdf2image` + `poppler` (system-installed; renders PDF pages to PNG for FR-014). Already available on Linux runners via apt; macOS via Homebrew `poppler`.
**Storage**: Filesystem only — `state/projects/<id>.yaml`, `state/run-log/<YYYY-MM>/<run-id>.jsonl`, `state/audit/pdf/<YYYY-MM-DD>/<paper-id>.json`, `state/audit/pdf/_quarantine/<YYYY-MM-DD>/<paper-path>`, `state/personality_rotation.yaml`. No database. Adjacent-work liveness cache at `state/audit/liveness-cache.json` (7-day TTL keyed by pointer string).
**Testing**: `pytest` (unit + real-call + phase2). Real-call coverage required per Constitution Principle III; mocks permitted only as a secondary fast-feedback layer alongside the real test.
**Target Platform**: Linux GitHub Actions runners (cron + PR CI), macOS dev laptops (Darwin 25.3).
**Project Type**: CLI + pipeline library (single package: `src/llmxive/`).
**Performance Goals**:
- Personality liveness check: ≤10s budget per pointer (configurable via `LIVENESS_TIMEOUT_SEC`, default 10).
- PDF audit: ≤120s per PDF average (FR-014 page-render + checks).
- Scheduler: advance ≥50 projects/day in steady state once `PIPELINE_PARALLELISM=8` is in place (SC-005).
**Constraints**:
- **Zero LLM calls in PDF pipeline** (Constitution + spec 009 FR-019 + this spec FR-013/SC-007). Enforced by the static AST test that walks every `.py` under `src/llmxive/pipeline/pdf_pipeline/` and asserts no banned imports.
- **No new paid dependencies** (Principle IV). All new deps are free/OSS.
- **All artifact writes guarded** by `_real_only_guard.assert_real_or_raise()` (FR-010).
**Scale/Scope**:
- 576 projects, 81 personality contributions, 159 PDFs (current audit set).
- Cron tick every 30 minutes (personality) and 60 minutes (intake); per-tick parallelism cap 8.
- ~25 new files + ~10 modified files expected (see Project Structure below).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Single Source of Truth (NON-NEGOTIABLE) — PASS

- `_real_only_guard` (spec 009) is the single canonical real/template classifier; this feature extends its *coverage* (call it everywhere), not its logic. No parallel classifier introduced.
- The personality rubric (`src/llmxive/audit/personality_rubric.py`) is the single canonical contribution-validation function; this feature extends it with three new axes in-place, not via a parallel rubric.
- Liveness check shared via a single module `src/llmxive/audit/liveness.py` used by both the personality rubric and any future caller (no inline `requests.head` calls anywhere else).
- PDF audit script lives at `src/llmxive/pipeline/pdf_pipeline/audit.py` and is the single audit entrypoint; its checkers reuse the same canonical macros (`\authorblock`, `\figwidth`, numeric square-bracket cites) that the normalizers enforce.

### II. Verified Accuracy (NON-NEGOTIABLE) — PASS

- Liveness check verifies adjacent-work pointers against primary sources (arXiv, DOI resolver, raw URL) — this directly *implements* the Verified-Accuracy principle for personality citations.
- PDF audit verifies rendered output against the spec, not against an LLM's opinion.
- All new tests run real HTTP HEAD against live arXiv / DOI (gated by network), with a fixture cache for offline replay.

### III. Robustness & Reliability (Real-World Testing) — PASS

- Personality rubric tests: real call to live arXiv via `requests.head` (network-dependent, gated by `LLMXIVE_NETWORK_TESTS=1`); offline replay via the cache JSON for CI runs without network.
- PDF audit tests: real `pdf2image` rendering of fixture PDFs + checker output snapshots, no mocked rasterizers.
- Scheduler tests: real `state/projects/*.yaml` files in a temp dir with concurrent advancement.
- Speckit prune tests: real `projects/<id>/specs/*/` fixtures (TEMPLATE + REAL) with real `_real_only_guard` calls.

### IV. Cost Effectiveness (Free-First) — PASS

- Zero new paid services. `pdf2image` + `poppler` are OSS; `requests` already in deps.
- Liveness cache (7-day TTL) avoids hammering arXiv / DOI.
- PDF audit runs on free GitHub Actions minutes.

### V. Fail Fast — PASS

- `_real_only_guard.assert_real_or_raise()` (spec 009 FR-009) already raises `TemplateRefused` BEFORE any expensive downstream artifact is written; FR-011 extends this with a two-strike escalation to `human_input_needed`.
- PDF audit fail-fast: missing `poppler` or `pdf2image` raises with an actionable install message before scanning any PDF.
- Personality liveness check: 10s timeout → reject contribution before disk write.
- Scheduler concurrency cap reads `PIPELINE_PARALLELISM` at process start; invalid value raises immediately.

### Verdict

No principle violations. No Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/010-personality-taste-speckit-real-pdf-audit/
├── plan.md                  # This file
├── research.md              # Phase 0 output
├── data-model.md            # Phase 1 output
├── quickstart.md            # Phase 1 output
├── contracts/               # Phase 1 output
│   ├── personality_contribution.schema.json
│   ├── speckit_artifact_audit.schema.json
│   └── pdf_audit_report.schema.json
├── checklists/
│   └── requirements.md      # Already written; passes all 16 items
└── tasks.md                 # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
src/llmxive/
├── audit/
│   ├── personality_rubric.py   # MODIFY: extend with FR-001/002/003 axes
│   ├── liveness.py             # NEW: HEAD-check arXiv/DOI/URL, 7-day cache
│   └── speckit_prune.py        # NEW: scan + delete templates transitively
├── agents/
│   └── personality.py          # MODIFY: position field in frontmatter,
│                               #   rotation diversity bias (FR-006)
├── pipeline/
│   ├── scheduler.py            # MODIFY: PIPELINE_PARALLELISM cap (FR-012)
│   ├── graph.py                # MODIFY: two-strike escalation to
│                               #   HUMAN_INPUT_NEEDED on TemplateRefused (FR-011)
│   └── pdf_pipeline/
│       ├── audit.py            # NEW: deterministic page-image audit (FR-014..21)
│       ├── classify_failure.py # NEW: failure → {source_fixable,
│                               #   unsupported_construct, source_missing}
│       └── cli.py              # MODIFY: add 'audit' subcommand
├── speckit/
│   └── _real_only_guard.py     # No logic change; usage extended via prune.py
├── agents/prompts/
│   ├── personality.md          # MODIFY: require position + interest_signal
│   └── personalities/*.md      # MODIFY: declare interest_signals in frontmatter
└── cli.py                      # No change

state/
├── audit/
│   ├── pdf/<YYYY-MM-DD>/<paper-id>.json   # per-PDF audit report
│   ├── pdf/_quarantine/<YYYY-MM-DD>/...    # crash quarantine
│   └── liveness-cache.json                # 7-day pointer cache
├── projects/<id>.yaml                     # MODIFY: roll stages back for purged projects
└── personality_rotation.yaml              # MODIFY (runtime): diversity bias state

tests/
├── unit/
│   ├── test_personality_rubric_axes.py     # NEW: FR-001/002/003 axes
│   ├── test_liveness_check.py              # NEW: arXiv/DOI/URL HEAD + cache
│   ├── test_speckit_prune.py               # NEW: TEMPLATE/REAL prune fixtures
│   ├── test_scheduler_parallelism.py       # NEW: concurrent advancement
│   ├── test_pdf_audit_page_checks.py       # NEW: per-failure-class fixtures
│   └── test_pdf_audit_quarantine.py        # NEW: crash-tolerant
└── real_call/
    ├── test_personality_liveness_real.py   # network-gated arXiv/DOI HEAD
    └── test_pdf_audit_real.py              # render real fixture PDFs
```

**Structure Decision**: Single Python package (`src/llmxive/`) with the existing module layout (`audit/`, `agents/`, `pipeline/`, `speckit/`). No new top-level packages. Tests follow the existing `tests/unit/` + `tests/real_call/` convention.

## Phase 0 — Research

See `research.md`. The research phase resolves three open architectural questions left by the spec's NEEDS-CLARIFICATION-free state:

1. **Personality prompt-engineering**: how to phrase the new requirements (position + adjacent-work pointer + interest-signal anchor) so the persona prompt actually *produces* them on the first attempt, rather than relying on rejection-and-retry. Decision: introduce a structured `Required outputs` section at the top of the umbrella prompt with an explicit example block per persona.

2. **Stage-rollback ordering** when a template is pruned: how to identify the "latest surviving stage with real artifacts" given the existing `STAGE_TO_AGENT` dependency graph in `src/llmxive/pipeline/graph.py`. Decision: walk back through the project's `history.jsonl` and find the most recent stage whose generated artifact still exists AND classifies REAL.

3. **PDF page-image checker primitives**: which image-level checks are deterministic vs. heuristic. Decision: text-extracted check for literal `\command{...}` strings and citation glyphs (deterministic via `pdfminer.six`); pixel-level check only for figure widths (measured at the rendered image level via `pdf2image` + bounding-box analysis).

## Phase 1 — Design & Contracts

### Data Model

See `data-model.md`. Three entity additions:

- **Personality contribution frontmatter** (extended): `position` field, optional `confidence` field, existing `persona`, `date`, `project_id`.
- **Speckit artifact audit record**: a row per artifact with `path`, `classification` (REAL / TEMPLATE), `reason`, `transitive_dependencies` (list of artifact paths whose generation depended on this one).
- **PDF audit report**: per-PDF JSON with `pdf_path`, `total_pages`, `pages[].status` (pass / fail), `pages[].failures` (list of failure-class entries), `summary.{total_failures,classification_counts}`.

### Contracts

See `contracts/`. Three JSON schemas:

- `personality_contribution.schema.json` — frontmatter shape
- `speckit_artifact_audit.schema.json` — audit row shape
- `pdf_audit_report.schema.json` — audit report shape

### Quickstart

See `quickstart.md`. Three runnable scenarios:

1. Generate one personality contribution end-to-end (umbrella prompt → rubric → liveness check → on-disk write).
2. Run the speckit-artifact prune in dry-run mode against the current repo (no deletions; just report).
3. Run the PDF audit against the current `docs/papers/` set (produces JSON reports under `state/audit/pdf/`).

### Agent Context Update

`CLAUDE.md` already contains a project-spec reference between `<!-- SPECKIT START -->` / `<!-- SPECKIT END -->` markers pointing to `specs/009-quality-fixes-pass/plan.md`. Update to point to `specs/010-personality-taste-speckit-real-pdf-audit/plan.md` in the post-Phase-1 step.

## Phase 2 — Tasks

Generated by `/speckit-tasks` from this plan + spec + research/data-model/contracts/quickstart. Not in scope for `/speckit-plan` output.

## Complexity Tracking

No constitution violations. No complexity-tracking entries.
