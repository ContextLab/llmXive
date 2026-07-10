# Implementation Plan: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Branch**: `001-evaluating-llm-docs-impact` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-evaluating-llm-docs-impact/spec.md`

## Summary

This project implements a feasibility pilot study to evaluate whether LLM-generated documentation reduces developer onboarding time and effort compared to human-written or no documentation. The technical approach involves: (1) a controlled experiment framework managing randomized participant assignment and logging; (2) an automated documentation generation pipeline using LLMs with fallback logic; and (3) a robust statistical analysis pipeline running on CPU-only constraints (≤7GB RAM, ≤6h). The study is designed as a pilot to estimate variance for future power-adequate studies, acknowledging limited statistical power for medium effect sizes with N=15-20.

**Key Methodological Updates**:
- **Causal Claim Restriction**: Primary causal inference is restricted to "LLM vs. None". "LLM vs. Human" is treated as an associational comparison with human doc quality as a covariate.
- **Robust Statistics**: Pre-specified Welch's ANOVA (Games-Howell post-hoc) to avoid "test-then-select" bias and handle small sample sizes.
- **Covariate Adjustment**: Repository complexity (LOC, CC) and Human Doc Quality are included as covariates in ANCOVA, replacing the infeasible "perfect matching" strategy.
- **Metric Validity**: "Clarification Questions" redefined as "Help Requests" (independent of struggle); "Cognitive Load Proxy" composite score added.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `scipy`, `pandas`, `numpy`, `requests`, `datasets`, `psutil`, `pyyaml`, `gitpython`  
**Storage**: Local filesystem (JSON/CSV/Parquet) for data; no persistent database required for this pilot  
**Testing**: `pytest` with contract tests against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier: vCPU, ~7GB RAM)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Analysis pipeline ≤6h runtime, ≤7GB peak RAM; Documentation generation ≤15min per repo (API dependent)  
**Constraints**: No GPU; no large-LLM training; CPU-only inference only; data subset to fit 7GB RAM  
**Scale/Scope**: Multiple conditions (LLM, Human, None); N=15-20 participants; ≤500 files per repository  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/analysis/` scripts; external datasets fetched from verified HuggingFace URL; repository commits pinned in `data/`; `requirements.txt` pins all dependencies. |
| **II. Verified Accuracy** | **PASS** | All citations (datasets, methods) validated against the `# Verified datasets` block in the spec; Reference-Validator Agent will check URLs before analysis. |
| **III. Data Hygiene** | **PASS** | Raw data (participant logs) preserved unchanged; derivations written to new files with checksums recorded in `state/`; PII scan enforced via `psutil`/custom script before analysis. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` generated directly from `data/` via `code/analysis/` scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for all `data/` and `code/` artifacts; `state/` updated on change; `experiment.py` logs LLM config with checksums. |
| **VI. Human Subjects Compliance** | **PASS** | IRB protocol referenced in `data/irb_protocol.sha256` (hash stored in `participant` schema); PII (names, emails) anonymized before analysis; consent records archived with restricted access. |
| **VII. Generation Traceability** | **PASS** | LLM config (model, version, temperature, prompt) logged in `data/llm_config.yaml` and checksummed alongside generated docs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-llm-docs-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/
├── data/
│   ├── raw/                  # Raw participant logs, unmodified
│   ├── processed/            # Anonymized, derived datasets
│   ├── repos/                # Pinned repository snapshots (commit hashes)
│   └── llm_config.yaml       # LLM generation config + checksum
├── code/
│   ├── experiment/
│   │   ├── experiment.py     # Main runner (US-1, FR-001, FR-003, FR-004)
│   │   └── participant_interface.py
│   ├── generation/
│   │   ├── doc_pipeline.py   # LLM doc generation (US-2, FR-002, FR-008)
│   │   └── repo_selector.py  # Repo selection & matching (FR-009)
│   ├── analysis/
│   │   ├── stats_runner.py   # Statistical tests (US-3, FR-005, FR-006)
│   │   └── report_gen.py     # Final report generation
│   └── utils/
│       ├── logging.py        # Time/memory monitoring (FR-010)
│       └── anonymize.py      # PII removal (Constitution VI)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/             # Schema validation tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure with modular `code/` directories for experiment, generation, and analysis. This minimizes overhead for a pilot study while maintaining separation of concerns. No database; all data stored as files for simplicity and reproducibility.

## Complexity Tracking

> **No violations found in Constitution Check. Complexity is justified by the need for: (1) randomization logic, (2) LLM fallback, (3) robust statistical tests, and (4) strict resource monitoring.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | N/A | N/A |

## Phase Plan (Computational Task Ordering)

1. **Phase 0: Research & Data Strategy** (`research.md`)
   - Verify dataset availability (none required for pilot; synthetic data for testing).
   - Select candidate repositories (≤500 files) with existing human docs.
   - Define LLM generation strategy (primary API + phi-2 fallback).
   - Confirm statistical methods (Pre-specified Welch's ANOVA with ANCOVA adjustment).

2. **Phase 1: Data Model & Contracts** (`data-model.md`, `contracts/`)
   - Define schemas for participant logs, repo metadata, and analysis outputs.
   - Create YAML contracts for validation.
   - Design data model for anonymization and IRB hash storage.

3. **Phase 2: Implementation** (Not covered here; handled by `/speckit-tasks`)
   - Implement `experiment.py`, `doc_pipeline.py`, `stats_runner.py`.
   - Implement resource monitoring (FR-010).
   - Implement PII anonymization (Constitution VI).

4. **Phase 3: Execution & Analysis**
   - Run mock study (N=3 simulated participants).
   - Generate docs for selected repos.
   - Execute statistical analysis on real/synthetic data.
   - Generate final report.

5. **Phase 4: Reporting**
   - Output `paper/` with figures/stats derived from `data/`.
   - Validate all citations.

## FR/SC Coverage Map

| FR/SC ID | Plan Element | Description |
|----------|--------------|-------------|
| FR-001 | `experiment.py` (Phase 2) | Randomized assignment of N≥15 participants to 3 conditions. |
| FR-002 | `doc_pipeline.py` (Phase 2) | LLM doc generation pinned to commit hash. |
| FR-003 | `experiment.py` (Phase 2) | Precise timestamp logging with high temporal resolution.. |
| FR-004 | `experiment.py` (Phase 2) | Clarification question logging (keyword + moderator tag). |
| FR-005 | `stats_runner.py` (Phase 2) | Pre-specified Welch's ANOVA with ANCOVA adjustment. |
| FR-006 | `stats_runner.py` (Phase 2) | Post-hoc corrections (Games-Howell). |
| FR-007 | `stats_runner.py` (Phase 2) | CPU-only execution, ≤6h, ≤7GB RAM. |
| FR-008 | `doc_pipeline.py` (Phase 2) | API fallback to phi-2 (int4) on failure. |
| FR-009 | `repo_selector.py` (Phase 2) | Repo selection with rubric (Setup/API/Arch) and LOC/CC measurement for ANCOVA. |
| FR-010 | `utils/logging.py` (Phase 2) | `time` + `psutil` monitoring. |
| SC-001 | `stats_runner.py` (Phase 2) | Time savings vs. "No Docs" baseline (causal). |
| SC-002 | `stats_runner.py` (Phase 2) | Question count reduction vs. "No Docs" (causal). |
| SC-003 | `stats_runner.py` (Phase 2) | Subjective ratings vs. "Human Docs" (associational). |
| SC-004 | `stats_runner.py` (Phase 2) | p-value < 0.05 threshold. |
| SC-005 | `utils/logging.py` (Phase 2) | Runtime/memory thresholds. |
| Edge Case (Abandon) | `experiment.py` (Phase 2) | Flag "incomplete", exclude from time analysis, retain for dropout reporting. |
| Edge Case (Stop-Loss) | `experiment.py` (Phase 2) | 45m timeout → "failed" with max_time=45m. |
| Edge Case (Repo Change) | `repo_selector.py` (Phase 2) | Pin commit hash for consistency. |
| Edge Case (Human Doc Variance) | `stats_runner.py` (Phase 2) | Include Human Doc Quality Score as covariate. |