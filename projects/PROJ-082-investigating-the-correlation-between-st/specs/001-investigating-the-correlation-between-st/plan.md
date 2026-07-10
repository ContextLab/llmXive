# Implementation Plan: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Branch**: `001-gene-regulation` | **Date**: 2023-10-27 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a meta-analysis pipeline to quantify the correlation between structural brain connectivity (dMRI metrics like FA/MD) and individual music preferences. The system prioritizes a quantitative random-effects meta-analysis if ≥10 eligible studies are found, calculating pooled effect sizes, heterogeneity (I²), and publication bias (Egger's test). **Crucially, if <10 studies are found, or if studies lack explicit (r, n) pairs, the system strictly pivots to a narrative systematic review.** The implementation strictly adheres to the project constitution's reproducibility and statistical integrity principles, running entirely on CPU-only GitHub Actions runners.

**Scientific Validity Note**: This project serves as a **Pipeline Validation** study. Synthetic data is used *only* to verify the code's ability to process statistical logic (recovery of known ground truth). The scientific conclusion regarding the real-world correlation is strictly conditional on the availability of real primary studies. If real data is insufficient, the output is a "Data Insufficient" narrative review, not a simulated correlation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: CSV (input), JSON (output), PNG (visualizations)  
**Testing**: `pytest` (unit tests on synthetic data, integration tests on mock meta-analysis)  
**Target Platform**: Linux (GitHub Actions default runner)  
**Project Type**: Data analysis library / CLI tool  
**Performance Goals**: Complete analysis of Numerous studies in <15 minutes; memory <7GB; disk <14GB.  
**Constraints**: No GPU; no deep learning; deterministic results via pinned random seeds; strict adherence to FR-001 (qualitative extraction) and FR-006 (narrative fallback).  
**Scale/Scope**: Input: A set of study records (synthetic or real); Output: A JSON report, a small set of plots.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All random seeds pinned in `code/`; `requirements.txt` pins exact versions; no external state changes. |
| **II. Verified Accuracy** | Citations in `research.md` link ONLY to verified dataset URLs provided in the prompt; no fabricated sources. |
| **III. Data Hygiene** | Input data is treated as immutable; derivations written to new files; PII scan via `Repository-Hygiene Agent`. |
| **IV. Single Source of Truth** | All statistics in `paper/` generated programmatically from `data/` JSON; no hand-typed numbers. |
| **V. Versioning Discipline** | Artifacts checksummed; `state/` updated on changes; `code/` versioned via git hash. |
| **VI. Meta-Analysis Statistical Integrity** | Random-effects model (`statsmodels`); I² calculated to multiple decimal places.; Egger's test only if N≥10; Bonferroni applied if N≥10 and k≥2 (with limitation note). |
| **VII. Systematic Review Fallback Protocol** | Code explicitly checks study count (N) before quantitative steps; if N<10, switches to narrative mode and skips aggregation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── study_record.schema.yaml
│   └── meta_analysis_result.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-082-investigating-the-correlation-between-st/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── main.py                 # Entry point for CLI
│   ├── extraction.py           # Data extraction (FR-001)
│   ├── meta_analysis.py        # Core stats (FR-002, FR-003, FR-005)
│   ├── visualization.py        # Plotting (FR-004, FR-006)
│   ├── utils.py                # Helpers, seeds, file I/O
│   └── fallback.py             # Narrative synthesis logic (FR-006)
├── data/
│   ├── raw/                    # Input CSVs (mock or real)
│   └── processed/              # Derived JSONs and PNGs
├── tests/
│   ├── unit/
│   │   ├── test_extraction.py
│   │   ├── test_meta_analysis.py
│   │   └── test_visualization.py
│   └── integration/
│       └── test_full_pipeline.py
└── paper/
    └── results.json            # Final report (Single Source of Truth)
```

**Structure Decision**: Single project structure (DEFAULT) selected. The project is a self-contained analysis pipeline. No frontend/backend split is required. The `code/` directory contains all logic, `tests/` for verification, and `data/` for inputs/outputs. This minimizes complexity and aligns with the "lightweight" nature of the meta-analysis.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | No violations found. The plan strictly adheres to the spec and constitution. | N/A |

## Phase Plan

### Phase 0: Research & Data Strategy
- **Goal**: Identify verified datasets and define the extraction logic for qualitative descriptors.
- **Tasks**:
  - Review verified dataset list (PubMed, MRI) for relevance to dMRI + Music Preference.
  - Define **specific regex/NLP logic** for extracting "qualitative descriptors" from abstract text (addressing T013).
    - *Logic*: Search for tract names (e.g., "arcuate", "cingulum") in proximity to directional verbs ("increased", "decreased", "correlated").
  - Confirm `statsmodels` random-effects implementation details.
  - Define the **Narrative Synthesis Methodology** (coding scheme for thematic analysis) to ensure rigor if N < 10.

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for `StudyRecord` and `MetaAnalysisResult`.
- **Tasks**:
  - Create `contracts/study_record.schema.yaml` with fields for `author`, `year`, `tract`, `r`, `n`, `qualitative_desc`.
  - Create `contracts/meta_analysis_result.schema.yaml` with fields for `pooled_r`, `ci_lower`, `ci_upper`, `i_squared`, `egger_p`, `egger_skipped_reason` (addressing T021).
  - Define output schema for PNG files (size <5MB).

### Phase 2: Implementation
- **Goal**: Implement extraction, analysis, and visualization modules.
- **Tasks**:
  - Implement `extraction.py` with fallback to narrative mode if N<10 (FR-006).
    - *Constraint*: If 'r' or 'n' missing, exclude from quantitative pool; include in narrative pool.
  - Implement `meta_analysis.py` with I² (**2 decimal places**, addressing T019) and Egger's test (conditional on N≥10).
    - *Constraint*: If N<10, output exact string: `"Skipped: Insufficient studies (N < 10) for Egger's regression."` (addressing T021).
  - Implement Bonferroni correction logic (FR-005) only if N≥10 and k≥2.
    - *Constraint*: Generate a mandatory "Limitations" note in the output report acknowledging that Bonferroni is conservative due to tract non-independence (addressing T022).
  - Implement `visualization.py` with memory checks and file size validation (SC-003, T031).
  - Implement `fallback.py` for narrative synthesis generation using the defined thematic coding scheme.

### Phase 3: Testing & Validation
- **Goal**: Verify all acceptance scenarios.
- **Tasks**:
  - Run unit tests on synthetic data (mock studies, missing values, bias scenarios).
  - Verify I² precision (T019) and Egger's skip message (T021).
  - **Verify PNG file sizes < 5MB** (SC-003, T031).
  - Confirm Bonferroni logic vs. RVE contradiction (T022) is resolved by implementing Bonferroni as per spec FR-005 with a limitation note.
  - Verify that if N < 10, the quantitative pooled estimate is suppressed or flagged as "unreliable" due to heterogeneity.

### Phase 4: Documentation & Handoff
- **Goal**: Finalize `quickstart.md` and `research.md`.
- **Tasks**:
  - Document setup, usage, and expected outputs.
  - Ensure all citations in `research.md` match verified URLs.
  - Document the "Pipeline Validation" nature of the synthetic data tests.

