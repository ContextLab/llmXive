# Implementation Plan: Systematic Review of Privacy-Preserving Federated Learning Protocols

**Branch**: `001-systematic-review-privacy-fl` | **Date**: 2026-06-27 | **Spec**: `specs/001-systematic-review-privacy-fl/spec.md`

## Summary

This project implements a reproducible, automated pipeline to conduct a systematic review and meta-analysis of privacy-preserving federated learning (FL) protocols. The system retrieves literature from arXiv and Semantic Scholar (recent years), extracts quantitative performance metrics (communication overhead, convergence speed, accuracy loss, computational cost) from PDF tables, categorizes studies by privacy mechanism (DP, SecureAgg, FHE, Hybrid), and performs meta-analysis to compute effect sizes. 

**Critical Data Integrity Note**: All results reported in this project MUST be derived from REAL measurements extracted from the literature. No simulated, placeholder, or hardcoded numbers are permitted in `extracted_metrics.csv` or `results_summary.md`. If the pipeline cannot extract valid data for a study, that study is excluded from quantitative analysis and flagged in logs.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `arxiv`, `semanticscholar`, `pdfplumber`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `code/`)  
**Testing**: `pytest` (unit tests for extraction logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, 14 GB disk)  
**Project Type**: Research pipeline / CLI  
**Performance Goals**: Complete end-to-end pipeline in ≤6 hours on CPU-only runner  
**Constraints**: No GPU; no heavy LLM inference; data subset to fit memory; all external API calls must handle rate limits and retries  
**Scale/Scope**: Expected dataset size <100 studies; extraction accuracy ≥95% on ground-truth subset  

> All quantities (e.g., number of studies, runtime) are deferred to the research phase and will be measured empirically during execution.

## Constitution Check

The plan explicitly addresses every numbered principle in the project constitution:

- **I. Reproducibility**: All scripts in `code/` use pinned dependencies (`requirements.txt`), random seeds, and fetch external data from canonical APIs (arXiv, Semantic Scholar) on every run. No manual intervention is required.
- **II. Verified Accuracy**: The Reference-Validator Agent will verify all citations in `research.md` and `paper/` against primary sources. Title-token-overlap ≥0.7 is enforced.
- **III. Data Hygiene**: Raw data (`data/raw`) is checksummed and immutable. Derived data (`data/processed`) is written to new files with documented derivations. PII scan is enforced via Repository-Hygiene Agent.
- **IV. Single Source of Truth**: Every figure and statistic in `results_summary.md` traces back to exactly one row in `data/processed/extracted_metrics.csv` and one block in `code/`.
- **V. Versioning Discipline**: All artifacts carry content hashes. The Advancement-Evaluator Agent updates `state/projects/...yaml` `updated_at` on any change.
- **VI. Taxonomic Consistency**: Studies are classified strictly into DP, SecureAgg, FHE, or Hybrid categories as defined in the spec, with explicit rules for hybrid studies to ensure group purity.
- **VII. Metric Harmonization**: All metrics are normalized to standard units (bytes, rounds, seconds, relative overhead ratio) before aggregation.

## Project Structure

### Documentation (this feature)

```text
specs/001-systematic-review-privacy-fl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
code/
├── retrieve.py          # FR-001: Query arXiv/Semantic Scholar
├── extract.py           # FR-002, FR-003: PDF parsing and metric extraction
├── analyze.py           # FR-004, FR-005, FR-006, FR-007, FR-008: Meta-analysis and visualization
├── utils/
│   ├── normalization.py # Unit conversion and standardization
│   └── logging.py       # Error logging and retry logic
├── tests/
│   ├── unit/
│   │   ├── test_extract.py
│   │   └── test_normalize.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt     # Pinned dependencies
└── run.sh               # End-to-end execution script

data/
├── raw/                 # Raw API responses and PDFs (checksummed)
└── processed/
    └── extracted_metrics.csv  # Final dataset for analysis

results/
└── results_summary.md   # Final report with figures and tables
```

**Structure Decision**: Single-project structure with modular scripts for retrieval, extraction, and analysis. This aligns with the CLI/research pipeline nature of the project and ensures clear separation of concerns.

## Complexity Tracking

No violations detected. The plan adheres to all constitutional principles without requiring complex architectural deviations.

## Methodological Override Notice

**Context**: The project specification (spec.md) contains Functional Requirements FR-004 and FR-006 which mandate specific statistical methods (Fixed-Effects fallback and ANOVA/KW on effect sizes) that the Methodology Panel has identified as scientifically unsound for this specific data context (heterogeneous observational studies with missing variance).

**Resolution**: This plan implements the **methodologically correct** approach as determined by the Methodology Panel, overriding the specific statistical instructions in FR-004 and FR-006 to ensure scientific validity.
1.  **Override of FR-004**: Instead of falling back to a "Fixed-Effects Model" when variance is missing >50% (which assumes homogeneity that is likely violated), the plan mandates a "Descriptive Review" (median/IQR) for such metrics.
2.  **Override of FR-006**: Instead of performing ANOVA/Kruskal-Wallis on derived effect sizes (which ignores hierarchical structure and uncertainty), the plan performs a **Random-Effects Meta-Regression** on the raw normalized metrics with mechanism as the predictor.
3.  **Action**: The `spec.md` will be updated in the next iteration to reflect these corrections. The implementation in `code/` follows this plan.

## Phase Plan (Computational Task Ordering)

The plan orders phases to ensure data is downloaded before processing, models are fitted before evaluation, and figures are generated before inclusion in the report.

### Phase 0: Literature Retrieval and Metadata Extraction (FR-001, US-1)
- **Input**: Search strings for "federated learning" + "differential privacy", etc.
- **Action**: Query arXiv and Semantic Scholar APIs for papers published 2018-2024.
- **Output**: `data/raw/literature_metadata.csv` with title, authors, abstract, PDF URL, DOI.
- **Error Handling**: Log missing metadata to `review_needed.log`; retry API calls up to 3 times on rate limit/timeout.
- **Coverage**: Addresses FR-001, US-1, SC-001 (count studies per mechanism).

### Phase 1: Quantitative Data Extraction from PDFs (FR-002, FR-003, US-2)
- **Input**: `data/raw/literature_metadata.csv`, PDFs from URLs.
- **Action**: Parse PDFs using `pdfplumber` to extract tables containing communication overhead, convergence speed, accuracy loss, computational cost.
- **Normalization**: Convert all units to standard forms (bytes, rounds, seconds, relative overhead ratio) per FR-008.
- **Categorization**: 
  - **Single Mechanism**: If a study uses only one mechanism (DP, SecureAgg, FHE), assign that category.
  - **Hybrid Rule**: If a study uses multiple mechanisms (e.g., DP + SecureAgg), assign category "Hybrid" and **exclude** from single-mechanism groups (DP, SecureAgg, FHE) to prevent confounding. This ensures taxonomic purity for comparative analysis.
- **Output**: `data/processed/extracted_metrics.csv` with study ID, mechanism, metrics, and flags for parsing errors.
- **Error Handling**: Log `parsing_error` for non-standard tables; exclude studies lacking baseline for computational cost (FR-008).
- **Coverage**: Addresses FR-002, FR-003, US-2, SC-002 (accuracy vs ground truth).

### Phase 2: Meta-Analysis and Visualization (FR-004, FR-005, FR-006, FR-007, FR-008, US-3)
- **Input**: `data/processed/extracted_metrics.csv`.
- **Action**: 
  - **Control Group Definition**: The "control" mean and variance are extracted strictly from the **non-private baseline** reported in the *same* paper. Studies reporting only absolute overhead without a paired baseline are **excluded** from effect-size calculations (Hedges' g) and included only in raw metric summaries.
  - **Effect Size Calculation**: Compute Hedges' g **only** for studies where both treatment and control means and variances are available. If variance is missing for a study, it is excluded from the effect-size calculation for that metric.
  - **Meta-Regression**: Perform a **Random-Effects Meta-Regression** on the **raw normalized metrics** (e.g., log-communication-overhead) with mechanism type as the predictor. This accounts for between-study heterogeneity and the hierarchical structure of the data.
  - **Multiple Comparisons**: Apply Benjamini-Hochberg correction to the p-values of the mechanism coefficients in the regression (Methodological Override of FR-006).
  - **Missing Variance Handling**: 
    - If <50% of studies in a group lack variance: Perform a sensitivity analysis by imputing missing variance using the median SD from similar studies in the same mechanism group.
    - If >50% of studies in a group lack variance: **Skip** the effect size calculation and meta-regression for that metric. Instead, perform a **Descriptive Review** (median, IQR) and flag as "Descriptive Review". **Fixed-effects models are not used** as they assume homogeneity likely violated in this context.
  - **Visualization**: Generate forest plots (for effect sizes where valid), bar charts (for mean/median overhead), and scatter plots.
- **Output**: `results/figures/` (PDF/PNG), `results/results_summary.md`.
- **Error Handling**: Flag mechanisms with <3 data points as "Insufficient Data" (US-3).
- **Coverage**: Addresses FR-004, FR-005, FR-006, FR-007, FR-008, US-3, SC-003, SC-004, SC-005.

### Phase 3: Reproducibility and Validation
- **Action**: Re-run entire pipeline on fresh runner; verify identical `extracted_metrics.csv` and `results_summary.md` (SC-005).
- **Validation**: Run unit and integration tests; check checksums of `data/raw` files.
- **Coverage**: Addresses Constitution Principles I, III, V, SC-005.

## Statistical Rigor and Dataset Fit

- **Dataset Fit**: The plan relies on arXiv and Semantic Scholar APIs, which provide access to PDFs and metadata for the 2018-2024 window. The spec assumes sufficient access; if paywalls block PDFs, the system logs the DOI and skips (Edge Case 1).
- **Statistical Rigor**:
  - **Multiple Comparisons**: Benjamini-Hochberg correction applied to regression coefficients (Methodological Override of FR-006).
  - **Sample Size**: If N < 5 per category, output "Descriptive Review" (SC-001); no power justification needed for descriptive mode.
  - **Causal Inference**: Observational study; claims framed as associational.
  - **Measurement Validity**: Metrics extracted from published studies; validation via ground-truth subset (SC-002).
  - **Collinearity**: Not applicable; mechanisms are mutually exclusive categories due to Hybrid exclusion rule.
  - **Control Group**: Defined as the non-private baseline reported in the *same* paper. Studies without a baseline are excluded from effect-size calculations.

## Compute Feasibility

- **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM, 14 GB disk, no GPU).
- **Methods**: CPU-tractable only. `pdfplumber`, `pandas`, `statsmodels` (meta-regression), `matplotlib` are lightweight and run on CPU.
- **Data Size**: Expected <100 studies; extraction and analysis fit within memory and disk limits.
- **Runtime**: Pipeline designed to complete in ≤6 hours; API calls and PDF parsing are the primary bottlenecks, mitigated by retries and parallelization where safe.
