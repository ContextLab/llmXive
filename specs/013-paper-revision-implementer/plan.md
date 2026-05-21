# Implementation Plan: Paper Revision Implementer + Publisher

**Branch**: `013-paper-revision-implementer` | **Date**: 2026-05-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/013-paper-revision-implementer/spec.md`

## Summary

Close the convergence loop spec 012 left open: an LLM-driven implementer
agent picks up `READY_FOR_IMPLEMENTATION` projects, applies each task in
the revision spec to `paper/source/main.tex` (and, for science-class
tasks, the project's research code), recompiles via the existing LaTeX
pipeline, and joins the paper's author list. After every reviewer
accepts, a deterministic `paper_publisher` agent regenerates the PDF
with the existing `llmxive.cls` byline rendering "Auto-Reviewed |
Auto-Revised | Published" + DOI + volume/issue, registers a real DOI
via Zenodo, appends the post-paper appendix (spacer + reviews +
revision changelog) to the PDF, and transitions the project to
`posted`. This is the brainstorm → write → review → revise → **publish**
end-to-end closure for the journal.

## Technical Context

**Language/Version**: Python 3.11 (project standard, per `pyproject.toml`)
**Primary Dependencies**:
- LaTeX build pipeline (existing `src/llmxive/pipeline/pdf_pipeline/` + `lualatex` + `bibtex` on PATH)
- `papers/.style/llmxive.cls` (already extended with `\paperdoi`, `\papervolume`, `\paperissue`, adjustbox auto-fit, tabularray)
- Dartmouth Chat API (default backend, `qwen.qwen3.5-122b` model, key resolved via `llmxive.credentials.load_dartmouth_key()`)
- Zenodo REST API (`https://zenodo.org/api/`) + Zenodo Sandbox (`https://sandbox.zenodo.org/api/`) for tests
- `requests` for HTTP, `pydantic` v2 for schemas, `yaml`/`tomllib` for config

**Storage**: filesystem-only (no database). Canonical state:
- `projects/<PROJ-ID>/paper/source/` (LaTeX manuscript — implementer edits here)
- `projects/<PROJ-ID>/paper/metadata.json` (authors, doi, volume, issue, zenodo_id)
- `projects/<PROJ-ID>/paper/publication.yaml` (authoritative publication metadata — NEW)
- `projects/<PROJ-ID>/paper/revision_history.yaml` (append-only round log)
- `projects/<PROJ-ID>/paper/.chunk_summaries/<sha>.txt` (chunked summary cache from spec-013 reviewer changes; already shipped)
- `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml` (per-task changelog)

**Testing**: pytest with two tiers:
- `tests/unit/` — deterministic, no network, runs in CI on every push
- `tests/real_call/` — gated on `LLMXIVE_REAL_TESTS=1`, exercises Dartmouth + Zenodo Sandbox

**Target Platform**: Linux + macOS CI runners (Github Actions). LaTeX toolchain via TeX Live.

**Project Type**: CLI + scheduler-driven agent (`llmxive run` orchestrates per-project tick).

**Performance Goals**:
- SC-001: 3-task fixture round completes in ≤10 min wall-clock
- SC-002: PROJ-578 (116 tasks) converges in ≤5 implementer rounds
- SC-006: Sandbox-Zenodo publication completes in ≤2 min wall-clock

**Constraints**:
- Implementer edits MUST be localized (unified-diff or search-and-replace pair). No whole-file rewrites (FR-005, FR-017).
- LaTeX MUST recompile after each task; on failure, roll back via git content-addressing (Assumptions).
- Zenodo token loaded from `~/.config/llmxive/credentials.toml::[zenodo].api_token` or `ZENODO_API_TOKEN` env (FR-031).
- Free-first: Zenodo (free, CERN-operated DataCite registrar) chosen over DataCite-direct ($1-2k/year) and Crossref (paid). See Constitution IV.

**Scale/Scope**:
- 6 user stories, 36 functional requirements (FR-001..FR-036), 8 success criteria.
- ~12 specialist reviewers per paper-review round (existing); 1 implementer + 1 publisher (NEW).
- Initial fixture: PROJ-578 (real arxiv-intake paper, 116 action items, currently parked).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-|-|-|
| **I. Single Source of Truth** | PASS | `paper/publication.yaml` is the single authoritative store for DOI/volume/issue; `metadata.json::doi` mirrors as convenience (FR-032). Author identity strings are canonical and deduplicated (FR-008). Existing `llmxive.cls` is extended in place — no parallel class. Existing LaTeX-build pipeline is reused, not duplicated (FR-010). |
| **II. Verified Accuracy** | PASS | DOI registration MUST go through real Zenodo API (FR-025); no mocked DOIs. Real-call SC-006 exercises Zenodo Sandbox. The publisher writes the DOI Zenodo RETURNS, not a fabricated one. Paper citations remain verified per existing reviewer pipeline. |
| **III. Robustness & Reliability** | PASS | SC-005 explicitly requires a real-call E2E test on the implementer; SC-006 on the publisher. Existing unit tests pass deterministically; real-call tests exercise live APIs. Tabular auto-fit and figure-cap changes ALREADY verified against the MemLens prototype (102-page PDF, all overflow eliminated). |
| **IV. Cost Effectiveness** | PASS | Zenodo is free (chosen over paid DataCite/Crossref — see Assumptions). Chunked-summarization cache (`paper/.chunk_summaries/`) amortizes LLM calls across 12 reviewers per paper. Dartmouth API is free for our use. |
| **V. Fail Fast** | PASS | FR-030: Zenodo API unreachable → stay at `paper_accepted`, retry on next tick, after 5 failures transition to `publish_blocked`. Credential loader raises on missing token (existing pattern in `llmxive.credentials`). Implementer aborts early on missing files (FR-003 step b); records "file-not-found" per FR-004. |

**Initial Gate Verdict**: PASS. No violations to record in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/013-paper-revision-implementer/
├── spec.md                 # Authoritative spec (shipped 2026-05-18)
├── plan.md                 # This file
├── research.md             # Phase 0 output — open-question resolution
├── data-model.md           # Phase 1 output — entity definitions + state transitions
├── quickstart.md           # Phase 1 output — operator-facing reproduction recipe
├── contracts/              # Phase 1 output — agent + filesystem + API contracts
│   ├── implementer-agent.md
│   ├── publisher-agent.md
│   ├── zenodo-api.md
│   ├── publication-yaml.md
│   ├── implementer-log-yaml.md
│   └── revision-history-yaml.md
├── checklists/             # /speckit-specify quality gate output (existing)
│   └── requirements.md
├── prototypes/             # End-to-end MemLens demo (102-page PDF) — shipped
│   ├── main-llmxive-published.tex / .pdf
│   ├── gen_appendix.py (production-equivalent appendix renderer)
│   ├── fix_appendix.py (legacy one-shot fixer)
│   └── 01-10 verification screenshots
└── tasks.md                # Phase 2 output (/speckit-tasks generates)
```

### Source Code (repository root)

```text
src/llmxive/
├── agents/
│   ├── paper_reviewer.py            # MODIFIED: chunked-summarization fallback already shipped (commit 3817c32b)
│   ├── advancement.py               # MODIFIED: paper_accepted → posted gate added (NEW for this spec)
│   ├── revision_planner.py          # UNCHANGED (spec 012)
│   ├── implementer.py               # NEW: llmXive-implementer agent (US1-3, FR-001..FR-019)
│   ├── publisher.py                 # NEW: paper_publisher agent (US6, FR-021..FR-033)
│   └── prompts/
│       ├── implementer.md           # NEW: LLM prompt for the implementer
│       └── implementer_edit.md      # NEW: per-task edit-generation prompt
├── pipeline/
│   ├── pdf_pipeline/                # UNCHANGED: existing LaTeX build (just reused)
│   ├── authors.py                   # NEW: append-only author management (FR-006..FR-008)
│   └── zenodo.py                    # NEW: Zenodo REST client (FR-025..FR-027, FR-031)
├── state/
│   ├── publication.py               # NEW: read/write paper/publication.yaml (FR-032)
│   └── revision_history.py          # NEW: append-only revision_history.yaml writer (FR-009)
├── scheduler.py                     # MODIFIED: pull READY_FOR_IMPLEMENTATION + paper_accepted out of _NEVER_PICK
└── credentials.py                   # MODIFIED: add load_zenodo_token() (mirrors load_dartmouth_key())

papers/.style/llmxive.cls            # MODIFIED: \paperdoi, \papervolume, \paperissue + auto-fit (already shipped, commit 3817c32b)

scripts/
├── extract_paper_content.py         # MODIFIED: wrapfigure width + [h]→[!htbp] (already shipped)
└── publish_paper.py                 # NEW: CLI wrapper `llmxive project republish <PROJ-ID>` (FR-030)

tests/
├── unit/
│   ├── test_paper_reviewer_arxiv_intake.py    # MODIFIED: chunked-summary tests already added (commit 3817c32b)
│   ├── test_implementer.py                    # NEW: unit tests for edit application + author dedupe
│   ├── test_publisher.py                      # NEW: unit tests for publication metadata + DOI handling
│   ├── test_authors.py                        # NEW
│   ├── test_publication.py                    # NEW
│   ├── test_revision_history.py               # NEW
│   └── test_advancement_posted.py             # NEW: paper_accepted → posted advancement
└── real_call/
    ├── test_paper_reviewer_chunk_summary.py   # SHIPPED (commit 3817c32b)
    ├── test_implementer_e2e.py                # NEW: SC-001 fixture
    └── test_publisher_zenodo_sandbox.py       # NEW: SC-006 sandbox publication
```

**Structure Decision**: Single-project Python package layout (`src/llmxive/...`).
The implementer and publisher are NEW agents added to the existing `agents/`
module; they share the `Agent`/`AgentContext` base class. The Zenodo client
is a new module under `pipeline/` because it's a pure I/O concern reused by
the publisher (not an agent itself). Author and publication state writers
live under `state/` alongside the existing `state/citations`/`state/reviews`
modules — consistent with the project's existing single-source-of-truth
filesystem layout.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-|-|-|

No constitution violations were identified. Complexity tracking is empty.

## Phase 0 — Outline & Research

Open questions (resolved in `research.md`):

1. **DOI registrar choice** — RESOLVED in spec Assumptions: Zenodo (free, CERN/DataCite-backed) over DataCite-direct (paid) and Crossref (paid). `research.md` documents the API + token + sandbox details.
2. **Implementer edit format** — RESOLVED in FR-005: structured `unified-diff` or `search-and-replace` pair. `research.md` documents the rationale + patch-application library choice (`difflib` + plain text replace; `git apply` for diffs).
3. **Rollback mechanism** — RESOLVED in Assumptions: `before_hash` per file via git's content-addressing. `research.md` documents the concrete recipe (`git stash`-free, pure-Python `Path.read_bytes()` snapshot).
4. **Author identity canonicalization** — RESOLVED in FR-008: `(name, agent_version)` dedupe key. `research.md` documents the canonical identity string format.
5. **DOI versioning on re-acceptance** — RESOLVED in FR-027: Zenodo `/actions/newversion` endpoint. `research.md` documents the API call sequence.
6. **Post-paper appendix typography** — RESOLVED in FR-035: same `llmxive.cls` style via `\include`d appendix.tex. `research.md` documents the merge approach + how `gen_appendix.py` produces the appendix tex.

**Output**: `research.md` with one entry per question (Decision / Rationale / Alternatives considered).

## Phase 1 — Design & Contracts

**Prerequisites**: `research.md` complete.

1. **Entities → `data-model.md`** (8 entities from spec):
   - `ImplementerAgent` (canonical identity + run config)
   - `ImplementerLog` entry (per-task outcome)
   - `RevisionHistory` entry (per-round summary)
   - `AuthorEntry` (extended schema for LLM-kind authors)
   - `PaperPublisher` (deterministic agent inputs/outputs)
   - `VolumeIssue` (derivation rule + storage)
   - `ZenodoDeposition` (Zenodo-side record reference)
   - `DOI` (identifier + URL pair)
   - State-transition diagram: `READY_FOR_IMPLEMENTATION → PAPER_REVIEW → PAPER_ACCEPTED → posted` with the `PAPER_REVISION_BLOCKED` and `publish_blocked` failure branches.

2. **Contracts → `contracts/`** (6 contracts):
   - `implementer-agent.md` — agent inputs (project_id, revision_spec_path), outputs (implementer-log, modified files, new PDF), invariants.
   - `publisher-agent.md` — agent inputs (project at `paper_accepted`), outputs (`publication.yaml`, new PDF, Zenodo deposition, `posted` transition).
   - `zenodo-api.md` — the REST endpoints the publisher hits (`POST /deposit/depositions`, `POST /actions/publish`, `POST /actions/newversion`) + sandbox vs production URL handling.
   - `publication-yaml.md` — schema for `paper/publication.yaml`.
   - `implementer-log-yaml.md` — schema for `implementer-log.yaml`.
   - `revision-history-yaml.md` — schema for `revision_history.yaml`.

3. **Quickstart → `quickstart.md`**: operator-facing instructions for
   - Running the implementer on a fixture project end-to-end
   - Driving the publisher against Zenodo Sandbox
   - Verifying the final PDF + DOI resolution
   - Recovering a `publish_blocked` project via `llmxive project republish`

4. **Agent context update**: update the `<!-- SPECKIT START --> ... <!-- SPECKIT END -->` block in `CLAUDE.md` to point to this plan.

**Output**: `data-model.md`, `contracts/*.md`, `quickstart.md`, updated `CLAUDE.md`.

## Post-Design Constitution Re-check

After Phase 1 artifacts exist, re-verify all 5 principles:

- **I. SoT**: `publication.yaml` is authoritative; metadata.json mirrors. Single canonical Zenodo client lives at `pipeline/zenodo.py` — no duplication.
- **II. Verified Accuracy**: All published DOIs come from Zenodo's real API response; no fabrication.
- **III. Robustness**: SC-005 + SC-006 real-call tests cover both new agents end-to-end.
- **IV. Cost**: Zenodo is free; chunked-summary cache amortizes LLM cost.
- **V. Fail Fast**: Token-missing, network-unreachable, and compile-after-rollback paths all raise/transition early per FR-030.

If any re-check fails post-design, return to Phase 1 and revise before invoking `/speckit-tasks`.
