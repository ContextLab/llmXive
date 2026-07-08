# Implementation Plan: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

**Branch**: `001-molecular-complexity-degradation` | **Date**: 2026-06-29 | **Spec**: `specs/001-molecular-complexity-degradation/spec.md`
**Input**: Feature specification from `/specs/001-molecular-complexity-degradation/spec.md`

## Summary

This project investigates the correlation between quantitative molecular complexity metrics (TPSA, rotatable bonds, graph spectral indices) and experimental degradation rates (half-lives) for FDA-approved small-molecule pharmaceuticals. The approach involves ingesting public datasets (Synthyra for structures), calculating descriptors via RDKit, and attempting to merge with verified degradation data sources.

**Critical Constraint**: No verified public dataset containing both FDA-approved structures and experimental degradation rates was identified in the source list. Consequently, this plan includes a mandatory **Data Availability Gate**. If the intersection of structural and degradation data is insufficient ($N < 30$), the statistical analysis phase is skipped, and the project outputs a "Data Insufficiency" report. No synthetic data will be generated for hypothesis testing.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `rdkit`, `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `datasets` (HuggingFace)  
**Storage**: Local CSV/Parquet files in `data/` (no external DB)  
**Testing**: `pytest` (unit tests for descriptor calculation, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7GB RAM)  
**Project Type**: Data Science / Computational Chemistry Pipeline  
**Performance Goals**: Complete full pipeline (ingest → analyze → report) within 6 hours; memory usage < 7GB.  
**Constraints**: No GPU; no large-LLM inference; dataset must be sampled or streamed if >7GB; **NO synthetic data for validation**.  
**Scale/Scope**: Subset of FDA-approved drugs (target: a representative range of molecules with valid degradation data). If unavailable, report N=0.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and canonical dataset URLs. |
| **II. Verified Accuracy** | **Compliant (with Data Gap Reported)** | Plan restricts dataset citations to the "Verified datasets" block. It explicitly reports the *absence* of degradation data rather than fabricating a source. |
| **III. Data Hygiene** | **Compliant** | Plan requires checksums for `data/` files and immutable raw data with derived files. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Plan includes content hashing for artifacts and `updated_at` tracking. |
| **VI. Cheminformatics Standardization** | **Compliant** | Plan mandates canonical SMILES via RDKit and consistent descriptor calculation. |
| **VII. Statistical Threshold Adherence** | **Compliant** | Plan enforces pre-defined thresholds (|r| ≥ 0.5, p < 0.05) and forbids post-hoc adjustment. |

## Project Structure

### Documentation (this feature)

```text
specs/001-molecular-complexity-degradation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-071-exploring-the-correlation-between-molecu/
├── data/
│   ├── raw/                  # Downloaded parquet/jsonl (immutable)
│   ├── processed/            # Merged, cleaned, standardized CSVs
│   └── checksums.txt         # SHA256 hashes for raw data
├── code/
│   ├── __init__.py
│   ├── ingest.py             # Data download, merging, and Data Availability Gate (US-1)
│   ├── descriptors.py        # RDKit calculation (US-1)
│   ├── standardize.py        # Unit conversion (no Arrhenius for pH) (US-2)
│   ├── analysis.py           # Correlation & Regression (US-2)
│   ├── viz.py                # Plot generation (US-3)
│   ├── report.py             # Markdown report generation (US-3)
│   └── insufficiency_report.py # Generates Data Insufficiency report if N < 30 (US-1)
├── tests/
│   ├── test_descriptors.py
│   ├── test_standardize.py
│   └── test_pipeline.py
├── data/
│   └── output_schema.yaml    # Contract for analysis output
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead. Data is processed in-memory or via chunked pandas operations to fit the 7GB RAM limit. The `code/` directory contains modular scripts for each user story, allowing isolated testing and execution.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| N/A | N/A | N/A |

## Phase Breakdown

### Phase 0: Data Ingestion & Availability Gate (FR-001, US-1)
1.  **Download**: Fetch FDA-approved drug structures from verified HuggingFace datasets (`Synthyra/FDA-Approved-Drugs`).
2.  **Verify Degradation**: Inspect the dataset for a column containing experimental degradation data (half-life, rate constant).
    -   **Gate**: If no such column exists, **HALT** analysis. Generate `data_insufficiency_report.md` and exit.
    -   **Gate**: If column exists but $N < 30$, **HALT** analysis. Generate `data_insufficiency_report.md` and exit.
3.  **Merge**: If data exists, join with structural data.
4.  **Filter**: Retain only FDA-approved small molecules with valid SMILES.

### Phase 1: Descriptor Calculation (FR-002, US-1)
1.  **Canonicalize**: Convert all SMILES to canonical form using RDKit.
2.  **Calculate**: Compute TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index.
3.  **Handle Errors**: Flag and exclude molecules where RDKit fails (non-standard valence), logging the SMILES.

### Phase 2: Data Standardization & Stratification (FR-008, FR-009, US-2)
1.  **Unit Conversion**: Convert rate constants ($k$) to half-life ($t_{1/2} = \ln(2)/k$) and standardize all time units to hours.
2.  **Normalization Check**:
    -   **Temperature**: Do NOT apply Arrhenius normalization as $E_a$ is unavailable.
    -   **pH**: Do NOT apply Arrhenius normalization as pH dependence is non-Arrhenius and requires specific kinetic data.
    -   **Strategy**: Stratify data by condition. Only records with conditions matching "Standard" (25°C, pH 7.4) are used for the primary regression. Records with other conditions are excluded from the primary model but included in a descriptive "Data Characteristics" table.
3.  **Filter**: Exclude records with missing degradation data.

### Phase 3: Statistical Analysis (FR-003, FR-004, FR-005, US-2)
1.  **Correlation**: Compute Pearson/Spearman matrices on the "Standard Condition" subset. Identify pairs with $|r| \ge $.
2.  **Regression**: Fit Multiple Linear Regression (MLR) and LASSO on the "Standard Condition" subset.
3.  **Cross-Validation**: Perform cross-validation to estimate generalizability.
4.  **Diagnostics**: Check residuals for normality (Shapiro-Wilk) and homoscedasticity (Breusch-Pagan).

### Phase 4: Visualization & Reporting (FR-006, FR-007, US-3)
1.  **Plotting**: Generate scatter plots with regression lines and residual diagnostics.
2.  **Reporting**: Generate a markdown report with methodology, coefficients, and version hashes.
3.  **Reproducibility**: Log dataset hashes and code versions.

## Compute Feasibility Strategy
- **Memory**: Use `pandas` with `dtype` optimization. If the merged dataset exceeds a substantial size threshold, implement a random sampling strategy (e.g., [deferred] sample) documented in `research.md`.
- **CPU**: Use `scikit-learn`'s default CPU implementations. No GPU acceleration.
- **Time**: Pipeline designed to run in < 6 hours. RDKit calculations are vectorized where possible.