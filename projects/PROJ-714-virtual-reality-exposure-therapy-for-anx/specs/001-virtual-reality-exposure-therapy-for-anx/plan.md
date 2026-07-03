# Implementation Plan: Virtual Reality Exposure Therapy Meta-Analysis

**Branch**: `001-vr-exposure-meta-analysis` | **Date**: 2026-06-25 | **Spec**: `specs/001-virtual-reality-exposure-meta-analysis/spec.md`

## Summary

This feature implements a reproducible, CPU-tractable meta-analysis pipeline to synthesize Randomized Controlled Trials (RCTs) comparing Virtual Reality (VR) Exposure Therapy to control conditions for anxiety disorders. The system executes a systematic literature search (simulated via CSV input for CI), extracts comparative statistics (means, SDs, Ns), computes Hedges' g effect sizes, and performs a random-effects meta-analysis using CPU-optimized libraries. The pipeline generates PRISMA flow diagrams, forest plots, publication bias assessments (Egger's test), and a comprehensive PDF report. The implementation strictly adheres to the project constitution's requirements for reproducibility, data hygiene, and verified accuracy, ensuring all results are derived from actual data processing rather than placeholders.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels` (for meta-analysis), `matplotlib`, `seaborn`, `reportlab` (PDF generation), `pyyaml`, `checksumdir`.  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`); CSV/JSON formats.  
**Testing**: `pytest` (unit tests for effect-size math, integration tests for pipeline flow).  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, 7GB RAM, No GPU).  
**Project Type**: Data Science Pipeline / Research Tool.  
**Performance Goals**: Full pipeline execution < 4 hours on CI; memory usage < 6GB.  
**Constraints**: No GPU; no external API calls that require keys during CI (search step uses CSV export); strict adherence to Hedges' g formula with small-sample correction; no simulated/placeholder results in final artifacts.  
**Scale/Scope**: Designed to handle up to 100 studies (typical meta-analysis size); optimized for datasets < 50MB.

> **Note on Computational Feasibility**: The plan explicitly avoids deep learning or large-LLM inference. All statistical operations (Hedges' g, random-effects models, Egger's test) are performed using standard linear algebra libraries (`numpy`, `scipy`) and `statsmodels`, which are trivially CPU-tractable.

**Protocol Adherence**:
- Search queries and inclusion criteria are **NOT hardcoded** in `code/`.
- Instead, they are loaded dynamically from `data/protocol.yaml` at runtime.
- `data/protocol.yaml` is a **static input file** that must exist before the pipeline runs.
- The content of `data/protocol.yaml` (search strings, criteria) is defined and locked **BEFORE** any data extraction or mock data generation to ensure compliance with Constitution Principle VI (Systematic Review Protocol Adherence).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Strategy |
|-----------|---------------------|
| **I. Reproducibility** | All scripts in `code/` will use pinned `requirements.txt`. Random seeds (e.g., `np.random.seed()`) will be set for any stochastic sampling (e.g., if bootstrapping is used for sensitivity). Search queries and inclusion criteria are loaded from `data/protocol.yaml` to ensure identical filtering on re-runs. |
| **II. Verified Accuracy** | The pipeline will not "invent" study data. It will process provided CSV exports. The `Reference-Validator` will check any external citations (e.g., Hedges & Olkin 1985) against the primary source before the report is finalized. **Specific Task**: Execute Reference-Validator script with inputs: Python `meta_analysis.py` output vs. pre-computed R script output (using `metafor` with REML estimator) to verify numerical equivalence. |
| **III. Data Hygiene** | Raw CSVs will be stored in `data/raw` with SHA-256 checksums recorded in `state/`. No in-place modifications; all derived data (effect sizes, meta-analysis results) written to new files in `data/processed`. PII scan enforced via pre-commit hooks. |
| **IV. Single Source of Truth** | All figures (forest plots, funnel plots) and statistics in the final PDF will be generated directly from the `data/processed` artifacts. No hand-typed numbers in the report. |
| **V. Versioning Discipline** | Content hashes for all `data/` and `code/` files will be tracked in `state/`. Any change to the analysis logic invalidates previous results. |
| **VI. Systematic Review Protocol** | A `protocol.md` will be created in `docs/` detailing the exact search strings, inclusion/exclusion criteria, and extraction logic. The executable parameters are stored in `data/protocol.yaml` which is loaded by the pipeline. This ensures the workflow is pre-registered and repeatable. |
| **VII. Effect-Size Reporting** | The output schema (see `contracts/`) mandates Hedges' g, confidence intervals, and I². The code will explicitly calculate and report these, flagging any studies missing data rather than imputing. |

## Project Structure

### Documentation (this feature)

```text
specs/001-virtual-reality-exposure-meta-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── study_schema.schema.yaml
│   ├── effect_size_schema.schema.yaml
│   └── meta_result_schema.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── search/
│   ├── query_builder.py       # Constructs search strings (from protocol.yaml)
│   └── csv_loader.py          # Loads and validates raw CSV exports
├── extraction/
│   ├── inclusion_filter.py    # Applies FR-002 criteria (from protocol.yaml)
│   └── effect_size_calc.py    # Implements Hedges' g (FR-003)
├── synthesis/
│   ├── meta_analysis.py       # Random-effects model (FR-004)
│   ├── bias_check.py          # Egger's test, funnel plots (FR-005)
│   └── sensitivity.py         # Leave-one-out (FR-006)
├── reporting/
│   ├── prisma_flow.py         # Generates PRISMA diagram (FR-007)
│   ├── forest_plot.py         # Generates forest plot
│   └── pdf_generator.py       # Compiles final report
├── main.py                    # Orchestrates the pipeline
└── requirements.txt           # Pinned dependencies
tests/
├── unit/
│   └── test_effect_size.py    # Validates Hedges' g math
└── integration/
    └── test_pipeline.py       # End-to-end run with mock data
data/
├── raw/                       # Unmodified CSV exports
├── processed/                 # Filtered studies, effect sizes
└── interim/                   # Intermediate calculation steps
```

**Structure Decision**: The single-project `code/` structure is selected to maintain simplicity and ensure all pipeline stages (search -> extract -> synthesize -> report) are tightly coupled and runnable in a single CI job. This minimizes overhead and ensures the "Single Source of Truth" principle is easily enforceable via a single `main.py` entry point.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separate Search/Extract/Synthesis Modules** | The systematic review protocol requires distinct, auditable stages. Separating search (data acquisition) from extraction (data cleaning) and synthesis (statistical modeling) ensures that a failure in one stage (e.g., bad CSV format) does not corrupt the statistical logic. | A monolithic script would make debugging specific FR-002 vs FR-003 failures difficult and violate the "Data Hygiene" principle of preserving raw data. |
| **PDF Report Generation** | Stakeholders require a single, portable document containing all figures and the PRISMA flow. | A collection of separate PNGs and CSVs is harder to review and does not meet the "Single Source of Truth" requirement for the final paper/report artifact. |

## Unresolved Panel Concerns Addressed

**Concern**: FABRICATED-RESULT signal — self-declared fabricated metric in tasks.md.
**Resolution**: The plan explicitly forbids the generation of placeholder results.
1.  **Data Strategy**: The pipeline will only process data present in `data/raw`. If the raw data is empty, the pipeline will halt with a "NO_CANDIDATE_STUDIES" status (as per Spec US-1) and generate a report stating "Zero studies included." It will **not** generate fake effect sizes.
2.  **Testing Strategy**: Unit tests (`tests/unit/test_effect_size.py`) will use *synthetic* math inputs to verify the *formula* (Hedges' g calculation) is correct, but the integration test (`tests/integration/test_pipeline.py`) will run against a *real* (or realistic mock) CSV file provided in the repo, ensuring the output is a genuine computation of that input data.
3.  **Output Contract**: The `meta_results.json` (or equivalent) will only contain values derived from the `effect_size_calc.py` module. If the input data is missing required columns, the study is excluded, and the exclusion is logged, not simulated.

**Concern**: Reliance on custom implementation for random-effects model.
**Resolution**: The plan now mandates the use of `statsmodels` for all meta-analytic modeling (REML and DL). A dedicated validation step (Task 0.5) is added to numerically verify the Python `statsmodels` implementation against a pre-computed R `metafor` benchmark on a fixed synthetic dataset before any production analysis. This eliminates the risk of implementation error associated with custom code.

## Phase Plan

### Phase 0: Research & Data Strategy
- **Goal**: Identify verified datasets, define the data extraction schema, and **lock the protocol**.
- **Tasks**:
  - **Task 0.1**: Define and lock `data/protocol.yaml` parameters (search strings, inclusion criteria) **BEFORE** generating `mock_studies.csv` or executing the search. This ensures the protocol is fixed prior to data exposure.
  - **Task 0.2**: Verify availability of open-access RCTs in PubMed Central/PsyArXiv (or define mock CSV schema for CI).
  - **Task 0.3**: Confirm the `metafor` equivalent in Python (`statsmodels.stats.meta_analysis`) is CPU-tractable and available in CI.
  - **Task 0.4**: Draft `protocol.md` with exact inclusion criteria.
  - **Task 0.5**: **Execute Validation**: Run `meta_analysis.py` (using `statsmodels` with `method='REML'`) on a fixed synthetic dataset (a small number of studies) and compare results against a pre-computed R `metafor` benchmark (using `rma.uni` with `method='REML'`). If the difference exceeds floating-point tolerance (e-6), the pipeline halts with a validation error. This ensures the statistical engine is correct before production use.

### Phase 1: Data Model & Contracts
- **Goal**: Define the strict schemas for Study, EffectSize, and MetaResult.
- **Tasks**:
  - Create `contracts/study_schema.schema.yaml` to validate raw CSVs.
  - Create `contracts/effect_size_schema.schema.yaml` to validate computed outputs.
  - Define the `data-model.md` with explicit column types and units.

### Phase 2: Implementation
- **Goal**: Build the pipeline scripts.
- **Tasks**:
  - Implement `csv_loader.py` and `inclusion_filter.py` (FR-001, FR-002) to load criteria from `data/protocol.yaml`.
  - Implement `effect_size_calc.py` (FR-003).
  - Implement `meta_analysis.py` (FR-004) using `statsmodels` with REML estimator.
  - Implement `bias_check.py` (FR-005) including **trim-and-fill logic** and ensure it populates the `trim_fill_adjusted_g` field in `meta_result.json`.
  - Implement `pdf_generator.py` and `prisma_flow.py` (FR-007).

### Phase 3: Verification & Reporting
- **Goal**: Run the pipeline and generate the final report.
- **Tasks**:
  - Execute the pipeline on a test dataset.
  - **Execute Reference-Validator**: Compare Python `meta_analysis.py` output (REML estimator) against pre-computed R script output (using `metafor` with REML estimator) to verify numerical equivalence on the actual test data.
  - Validate all figures and statistics against manual calculations.
  - Generate the final PDF report.
