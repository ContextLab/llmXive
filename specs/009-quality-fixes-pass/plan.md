# Implementation Plan: Quality Fixes — Personality Curation, Speckit Real-Output Enforcement, PDF Pipeline Hardening, Feedback-Loop Activity Feed

**Branch**: `009-quality-fixes-pass` | **Date**: 2026-05-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from [spec.md](spec.md)

## Summary

Four independently shippable user stories layered on top of existing llmXive infrastructure:

1. **Personality curation** — upgrade `agents/prompts/personality.md` and each persona card with explicit interest signals and a curation/taste pass; add a deterministic post-tick rubric validator; convert rubric-fail-after-retry into a logged `abstain` (rotation advances).
2. **Speckit real-output enforcement** — write a deterministic template-vs-real auditor for every artifact under `projects/PROJ-*/specs/**/`, prune `template`-classified artifacts in a single atomic commit, harden `src/llmxive/speckit/*.py` to refuse emitting stub artifacts (and refuse to accrue project progression points on non-emission), gate in CI.
3. **PDF pipeline hardening** — write a page-level PDF defect auditor (taxonomy in spec FR-012), fix `papers/.style/llmxive.cls` and the arxiv-restyle/compile scripts so every PDF in the corpus passes, enforce cite-order `[N]` references uniformly (FR-014, Clarification Q1), make the arxiv→PDF pipeline 100% LLM-free, auto-populate a "supported PDFs" registry from zero-defect papers (FR-022, Clarification Q2).
4. **Feedback-loop activity feed** — give every project a persisted, append-only, attributed activity feed; deliver it to every downstream agent dispatched against that project; require a "comments considered" manifest in every agent's output; gate manifest validity with a feedback-loop auditor.

Technical approach: extend existing Python codebase under `src/llmxive/`; reuse runner dispatch path (`src/llmxive/agents/runner.py`) as the single integration point for FR-026/FR-027; reuse existing test infrastructure under `tests/`; add four CLI auditors that double as CI jobs; gate everything through real-call tests per Constitution Principle III.

## Technical Context

**Language/Version**: Python 3.11 (existing project standard)
**Primary Dependencies**: existing — `pyyaml`, `requests`, `arxiv`, LaTeX toolchain (`lualatex`, `bibtex`), `pdftotext` (Poppler) for PDF auditing, `pdfplumber` for richer text+layout extraction, deterministic markdown parsing via `markdown-it-py`. No new paid services.
**Storage**: filesystem — markdown/yaml/json artifacts in `projects/PROJ-*/`, `papers/`, `specs/`, `agents/`; activity feeds as per-project append-only JSON Lines files (`projects/PROJ-XXX-*/activity.jsonl`). Maintainer audit logs as `projects/PROJ-XXX-*/.audit/*.jsonl` (gitignored from feed delivery but committed to repo).
**Testing**: pytest with the existing real-call layer (`tests/real_call/`, `tests/integration/`, `tests/unit/`); positive-and-negative fixture coverage for each auditor (FR-024).
**Target Platform**: Linux/macOS dev + GitHub Actions CI. No new OS dependencies beyond what `papers/.style/` already requires.
**Project Type**: Multi-module Python project (CLIs + cron-triggered agents + LaTeX pipeline). Single-repo layout.
**Performance Goals**:
  - PDF auditor: ≤30s per paper on the existing corpus; complete corpus audit in CI ≤10 min.
  - Speckit template auditor: ≤5s per artifact; complete `projects/` tree scan ≤2 min.
  - Personality rubric validator: ≤2s per contribution (deterministic string/regex scan).
  - Feedback-loop auditor: ≤1s per dispatch sample item.
**Constraints**:
  - No LLM call anywhere in the arxiv→PDF pipeline (spec FR-019, hard ban).
  - Auditors themselves are deterministic — LLM heuristics MAY augment but MUST NOT be the gating signal (spec Assumptions).
  - Constitution Principle IV (free-first) — no new paid SaaS; Poppler/`pdftotext` is open-source.
  - Constitution Principle V (fail-fast) — every auditor and every speckit emitter validates preconditions before doing expensive work.
**Scale/Scope**:
  - ~25 existing projects under `projects/`, ~10 personas, ~20 papers in `papers/`. Spec changes are within those scales for the initial fix pass; design supports growth.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Compliance evaluation | Status |
|-|-|-|
| **I. Single Source of Truth (NON-NEGOTIABLE)** | All four auditors share one CLI scaffold (`src/llmxive/audit/__init__.py` exposing `run_audit(name, …)`); template strings used by the speckit auditor are loaded from the existing `.specify/templates/*.md` (no duplication); the cite-order rendering rule is set once in `papers/.style/llmxive.cls` (no per-paper override); persona "interest signals" live in each persona card (one canonical place) and are loaded by the umbrella prompt, never inlined elsewhere. | PASS |
| **II. Verified Accuracy (NON-NEGOTIABLE)** | The PDF auditor verifies *rendered output*, not LLM claims about it; reference rendering is verified by re-running the deterministic pipeline against the source; the personality rubric counts concrete content tokens (specific objection markers, citations, adjacent-work pointers), not "vibe". No claim is allowed past an auditor without primary-source verification. | PASS |
| **III. Robustness & Reliability (Real-World Testing)** | Each auditor has a real-call test that runs the auditor against the actual `projects/`, `papers/`, and persona prompt files in the repo; PDF auditor tests use real PDFs in `papers/`; speckit emitter tests run the actual emitter and inspect the actual file emitted; feedback-loop auditor tests run a real dispatch through the runner with seeded comments. Mock tests, if added, are a secondary fast layer per Principle III's allowance. | PASS |
| **IV. Cost Effectiveness (Free-First)** | All new dependencies are open-source (Poppler/`pdftotext`, `pdfplumber`, `markdown-it-py`); auditors run on GitHub Actions free minutes; no LLM API calls added (the spec explicitly bans them in the PDF pipeline; the personality rubric is regex+heuristic, not LLM). | PASS |
| **V. Fail Fast** | Every emitter validates preconditions (template loaded, output directory writable, project context complete) before writing; every auditor validates inputs (file exists, parses) before scanning; activity feed dispatch fails immediately if the project's `activity.jsonl` is unreadable; PDF pipeline checks LaTeX toolchain on PATH before invoking it. | PASS |

**Result**: No violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/009-quality-fixes-pass/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already exists)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── audit-manifest.schema.json
│   ├── activity-feed-item.schema.json
│   ├── comments-considered-manifest.schema.json
│   ├── persona-card-frontmatter.schema.yaml
│   └── supported-pdfs-registry.schema.json
├── checklists/
│   └── requirements.md  # Existing quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/llmxive/
├── audit/                       # NEW — shared scaffold (Principle I)
│   ├── __init__.py
│   ├── cli.py                   # one CLI entrypoint, four subcommands
│   ├── personality_rubric.py    # FR-004, FR-005 (rubric validator)
│   ├── template_vs_real.py      # FR-006, FR-007 (speckit template auditor)
│   ├── pdf_auditor.py           # FR-012, FR-013 (PDF defect auditor)
│   ├── feedback_loop.py         # FR-034 (manifest + feed-delivery auditor)
│   └── manifest.py              # shared manifest writer (audit-manifest contract)
│
├── agents/
│   ├── personality.py            # MODIFY — load interest signals, run rubric, retry-once-then-abstain
│   ├── runner.py                 # MODIFY — load activity feed; inject into every agent dispatch (FR-026); validate manifest in output (FR-028)
│   └── (other agents stay)       # paper_writing, paper_reviewer, etc. — opt into runner's new dispatch path
│
├── speckit/
│   ├── analyze_cmd.py
│   ├── clarify_cmd.py
│   ├── implement_cmd.py
│   ├── plan_cmd.py
│   ├── specify_cmd.py
│   ├── tasks_cmd.py
│   ├── paper_*_cmd.py
│   └── _real_only_guard.py       # NEW — calls audit.template_vs_real before any commit; each *_cmd.py imports this guard directly (no central emitter — Principle I: one guard, all callers reach it)
│
├── feed/                         # NEW
│   ├── __init__.py
│   ├── store.py                  # append-only writer; reader; truncate-from-oldest packing (FR-031)
│   └── manifest.py               # "comments considered" manifest schema + validator (FR-027)
│
└── pipeline/
    └── pdf_pipeline/             # NEW — refactor of scripts/restyle_arxiv_paper.py + scripts/compile_paper.py into a deterministic Python module with CLI; explicitly no LLM imports (FR-019)
        ├── __init__.py
        ├── restyle.py
        ├── compile.py
        ├── normalize_references.py  # cite-order [N] normalization (FR-014)
        ├── normalize_figures.py     # FR-015
        ├── normalize_authors.py     # FR-016
        └── cli.py

agents/
├── prompts/
│   ├── personality.md            # MODIFY — taste/curation pass, manufactured-praise ban, feed-awareness (FR-001/FR-002/FR-029)
│   └── personalities/
│       └── *.md                  # MODIFY all 10 — add `interest_signals:` frontmatter (FR-003)

papers/
└── .style/
    └── llmxive.cls               # MODIFY — uniform author block (FR-016), bounded figure widths (FR-015), unsrt-style references (FR-014), section-numbering correctness (FR-018), custom-block handlers or fail-loud (FR-020)

projects/
├── PROJ-XXX-*/activity.jsonl     # NEW — per-project append-only feed
└── PROJ-XXX-*/.audit/            # NEW — rubric-rejected contributions, original-edit history

scripts/
├── audit_personalities.sh        # convenience wrappers — CI uses module directly
├── audit_speckit.sh
├── audit_pdfs.sh
└── audit_feedback_loop.sh

tests/
├── unit/
│   ├── test_audit_personality_rubric.py
│   ├── test_audit_template_vs_real.py
│   ├── test_audit_pdf.py
│   ├── test_audit_feedback_loop.py
│   ├── test_feed_store.py
│   ├── test_comments_considered_manifest.py
│   ├── test_pdf_pipeline_normalize_references.py
│   ├── test_pdf_pipeline_normalize_figures.py
│   └── test_pdf_pipeline_normalize_authors.py
├── integration/
│   ├── test_speckit_emitter_refuses_template.py
│   ├── test_personality_rubric_retry_then_abstain.py
│   ├── test_runner_injects_feed.py
│   └── test_runner_rejects_missing_manifest.py
├── real_call/
│   ├── test_pdf_pipeline_e2e_on_corpus.py
│   ├── test_audit_pdf_on_corpus.py
│   ├── test_personality_rotation_with_feed.py
│   └── test_seeded_project_revision_loop.py
└── fixtures/
    ├── audit/
    │   ├── speckit_template/        # known-template artifacts
    │   ├── speckit_real/            # known-real artifacts
    │   ├── pdf_clean/               # zero-defect PDFs (built from fixture sources)
    │   └── pdf_defective/           # PDFs with each defect type, one per defect
    └── feedback/
        ├── seeded_project/          # three known prior comments
        └── expected_manifests/

.github/workflows/
└── audit.yml                     # NEW — runs all four auditors on every push (FR-023, SC-009)
```

**Structure Decision**: Single-project layout (Option 1 from the template) consistent with existing `src/llmxive/` Python package. Four user stories each map to a sibling module under `src/llmxive/audit/` (shared scaffold per Principle I) plus targeted modifications to the relevant existing module (`agents/personality.py`, `agents/runner.py`, `speckit/*.py`, `papers/.style/llmxive.cls`).

## Phase 0 — Research

See [research.md](research.md). All Technical Context items resolved; no NEEDS CLARIFICATION remain.

## Phase 1 — Design & Contracts

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Constitution Re-Check (Post-Design)

After completing Phase 1 design:

| Principle | Re-evaluation | Status |
|-|-|-|
| I. Single Source of Truth | The `src/llmxive/audit/` package centralises auditor logic; the activity feed has exactly one writer (`feed/store.py`) and one reader; manifest schema lives in one place (`contracts/comments-considered-manifest.schema.json`) and is loaded by both the writer and the validator. | PASS |
| II. Verified Accuracy | Every auditor produces evidence-bearing reports (defect snippets, rule-fired citations, manifest item IDs) that allow a maintainer to verify each claim against the source artifact. | PASS |
| III. Real-World Testing | `tests/real_call/*` covers the corpus and the full personality rotation; integration tests exercise the actual emitter/runner code paths with real fixture files; no mock-only test gates the auditors. | PASS |
| IV. Free-First | No paid dependencies introduced; CI runs on GitHub Actions free tier. | PASS |
| V. Fail Fast | Every auditor, every emitter, and the runner's dispatch path validate preconditions before any expensive operation. | PASS |

**Result**: No regressions. Plan ready for `/speckit-tasks`.

## Phase 2 — Tasks

`/speckit-tasks` will generate [tasks.md](tasks.md) from this plan.
