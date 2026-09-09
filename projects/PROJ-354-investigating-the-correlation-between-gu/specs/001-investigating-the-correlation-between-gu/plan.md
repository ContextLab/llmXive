# Implementation Plan: Pipeline Validation for Gut Microbiome & Cognitive Function Analysis (Synthetic Data)

**Branch**: `001-gut-microbiome-cognitive` | **Date**: 2025-01-10 | **Spec**: `specs/001-gut-microbiome-cognitive/spec.md`

## Summary

This feature implements a **pipeline validation study** to demonstrate the statistical methodology (ILR transformation, linear regression with confounder control, Benjamini-Hochberg correction) for analyzing the association between gut microbiome composition and cognitive function. 

**Critical Feasibility Statement**: The original research question ("Investigating the Correlation...") requires real UK Biobank data. However, UK Biobank is access-gated and cannot be downloaded on the GitHub Actions free-tier runner. **No open-access proxy dataset exists that matches the required schema.** Therefore, this phase uses a **deterministic synthetic data generator** to validate the *pipeline logic* and *statistical code*. The biological hypothesis (that specific taxa correlate with cognition) **cannot be tested** in this phase and is deferred to a future phase requiring real data access. The success criteria for this phase are strictly limited to **code correctness** and **methodological soundness** on synthetic data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `biom-format`, `pyyaml`, `datasets` (HuggingFace), `seaborn`, `matplotlib`  
**Storage**: Local filesystem (streamed processing to fit ~14 GB disk); Parquet intermediate files  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Data Science Pipeline / Research Script  
**Performance Goals**: Process synthetic cohort within 6 hours; memory usage < 7 GB via streaming; CPU-bound linear models  
**Constraints**: No GPU; no external credentials at runtime; strict adherence to compositional data principles (ILR); no causal claims; **synthetic data used ONLY for pipeline logic validation**  

### Feasibility & Data Strategy

*   **UK Biobank Data**: Access-gated. Cannot be downloaded on CI. **Deferred** to real-data phase.
*   **Open Proxy Datasets**: None exist with matched microbiome + cognitive data.
*   **Synthetic Data Strategy**: A deterministic generator (`code/pipelines/download.py`) creates a dataset mimicking the UKB schema (Field IDs 20400, 20002, etc.) with realistic distributions.
    *   **Purpose**: Validate the *pipeline code* (ILR, regression, BH correction).
    *   **Limitation**: Cannot validate the *biological hypothesis* or *real-world statistical power*.
    *   **Transparency**: The `data-model.md` explicitly documents the synthetic nature.

### Reframed Objective

*   **Original**: "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data"
*   **Current Phase**: "Validating the Analysis Pipeline for Microbiome-Cognition Associations on Synthetic Data"
*   **Future Phase**: "Investigating the Correlation... on Real UK Biobank Data" (Requires credentials)

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Pass | Random seeds pinned in `code/utils/seeding.py`. Synthetic data generator is deterministic. Dependencies pinned in `pyproject.toml`. |
| **II. Verified Accuracy** | ✅ Pass | The citation "Gloor et al. (2017)" (referenced in research.md) will be verified by the Reference-Validator Agent. No dataset URLs are cited (synthetic data). |
| **III. Data Hygiene** | ✅ Pass | Synthetic data is generated fresh per run; checksums recorded. No PII (synthetic IDs). |
| **IV. Single Source of Truth** | ✅ Pass | All results trace to `data/processed` and `code/` scripts. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes for all artifacts updated on change. |
| **VI. Compositional Data Analysis Integrity** | ✅ Pass | ILR transformation is mandatory in `code/models/microbiome_transform.py`. **ILR is the "equivalent" method to CLR** mandated by this principle, producing orthonormal coordinates that break the sum-to-zero constraint. |
| **VII. Confounding Control Rigor** | ✅ Pass | All models include age, sex, BMI, diet, activity, meds. Reduced models for over-control are implemented. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gut-microbiome-cognitive/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-354-investigating-the-correlation-between-gu/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── seeding.py          # Random seed management
│   │   ├── streaming.py        # Data streaming helpers
│   │   └── validation.py       # Schema validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── microbiome_transform.py # ILR transformation
│   │   ├── association.py      # Linear models (OLS, Lasso, Ridge)
│   │   └── interaction.py      # Age-interaction models
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── download.py         # Implements 'Data Download Interface' by generating synthetic data when real data is inaccessible
│   │   ├── preprocess.py       # Filtering, ILR, aggregation
│   │   └── analyze.py          # Main analysis loop
│   └── paper/
│       ├── __init__.py
│       └── plots.py            # Manhattan plots, diagnostics
├── data/
│   ├── raw/                    # Generated synthetic raw data (checksummed)
│   ├── processed/              # ILR-transformed, filtered data
│   └── interim/                # Intermediate artifacts (cleaned up)
├── results/
│   ├── associations/           # Parquet of results
│   ├── plots/                  # Generated figures
│   ├── sensitivity/            # Threshold sweep results
│   └── power/                  # Power analysis outputs
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # Pipeline integration tests
│   └── unit/                   # Unit tests for transforms/models
├── pyproject.toml              # Dependencies and tool config
├── .ruff.toml                  # Linting config
└── requirements.txt            # Pinned dependencies
```

**Structure Decision**: Single project structure (Option 1) is selected. The project is a research pipeline, not a web service or mobile app. The separation of `models/`, `pipelines/`, and `utils/` ensures modularity and testability. `data/` is split into `raw`, `processed`, and `interim` to enforce the "no in-place modification" rule.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **ILR Transformation** | Mandatory for compositional data (Principle VI). | CLR or raw abundances produce spurious correlations; mathematically invalid for linear regression. |
| **Synthetic Data Generator** | UK Biobank data is access-gated; no open URL exists for CI. | Using a "fake" static CSV would fail reproducibility; a *generator* ensures deterministic, schema-compliant data for every run. |
| **Streaming/Chunking** | Full UK Biobank dataset exceeds typical disk/RAM limits. | Loading full dataset into memory would crash the runner; streaming allows processing the full logical cohort. |
| **Multiple Model Types (OLS, Lasso, Ridge)** | Required for robustness (FR-004, SC-006). | Single OLS model would not address multicollinearity or overfitting; Lasso/Ridge provide regularized estimates. |
| **Interaction Term Analysis** | Required to assess age-dependence without splitting sample (FR-006). | Stratification would reduce power in the 65+ group; interaction terms preserve the full sample size. |

## Task List & Ordering (Resolved Circular Dependencies)

*Note: T019 (Power Gate) is moved to Phase 2 and runs on a **mock** pipeline to validate the gate logic. The **real** pipeline implementation (T014-T018) runs in Phase 3.*

### Phase 0: Setup & Configuration
- [ ] **T001**: Create directory structure (`code/`, `data/`, `results/`, `tests/`). *Evidence: Directory tree listing.*
- [ ] **T002**: Create `pyproject.toml` with pinned dependencies.
- [ ] **T003**: Create `.ruff.toml` linting configuration. *Evidence: File content.*
- [ ] **T004**: Create `requirements.txt`.

### Phase 1: Data Generation (Synthetic)
- [ ] **T014**: Implement `code/pipelines/download.py` (Synthetic Generator). *Evidence: Script + sample output.*
- [ ] **T015**: Implement `code/utils/seeding.py`.
- [ ] **T016**: Implement `code/utils/streaming.py`.
- [ ] **T017**: Generate `data/raw/synthetic_ukb.parquet` (Seed 42).
- [ ] **T018**: Implement `code/pipelines/preprocess.py` (ILR Transformation).

### Phase 2: Validation Gate (Mock)
- [ ] **T019**: Run **Mock** Power Gate on a small synthetic subset to validate the *logic* of the power analysis script. *Evidence: Mock report.* (This breaks the circular dependency by not requiring the full pipeline).

### Phase 3: Core Analysis
- [ ] **T019.5**: Pre-screen taxa by prevalence (on real synthetic data).
- [ ] **T028**: Fit Lasso models for main effects.
- [ ] **T028b**: Fit OLS models [Parallel].
- [ ] **T028c**: Fit Ridge models [Parallel].
- [ ] **T021**: Apply Benjamini-Hochberg correction for main effects.
- [ ] **T024**: Fit Interaction models (Age_Group * Taxon).
- [ ] **T024c**: Apply BH correction for interaction terms.
- [ ] **T022a**: Fit Reduced Models (without diet/meds) for over-control bias.
- [ ] **T022b**: Generate Over-Control Bias Report.
- [ ] **T023**: Update metadata (causality_claim: false).

### Phase 4: Visualization & Sensitivity
- [ ] **T028a**: Generate Manhattan-style plots.
- [ ] **T029a**: Perform Threshold Sweep (p-value cutoffs: 0.01, 0.05, 0.1).
- [ ] **T033**: Generate Interaction Comparison Report.

### Phase 5: Documentation & Verification
- [ ] **T034**: Run Integration Tests.
- [ ] **T039**: Update `quickstart.md` and `README.md`.
- [ ] **T041**: Run `black` and `ruff`; generate linting report. *Evidence: Lint report.*
- [ ] **T042**: Performance optimization (streaming).
- [ ] **T043**: Verify `quickstart.md` instructions.

### Phase O: Review-Driven Revision
- [ ] **T050**: Address Reviewer Concerns (Methodology).
- [ ] **T051**: Address Reviewer Concerns (Data Resources).
- [ ] **T052**: Address Reviewer Concerns (Spec Coverage).

## Requirements Mapping (with Deferrals)

| Requirement | Status | Notes |
| :--- | :--- | :--- |
| **FR-001** (Download UKB) | ⚠️ Deferred | Implemented as "Download Interface" with synthetic fallback. **Real download deferred.** |
| **FR-002** (Filter Cohort) | ✅ Implemented | Filters antibiotic users in synthetic data. |
| **FR-003** (ILR Transform) | ✅ Implemented | Core methodology. |
| **FR-004** (Linear Models) | ✅ Implemented | OLS, Lasso, Ridge. |
| **FR-005** (BH Correction) | ✅ Implemented | FDR control. |
| **FR-006** (Interaction) | ✅ Implemented | Age_Group * Taxon. |
| **FR-007** (Manhattan Plots) | ✅ Implemented | Visualization. |
| **FR-008** (Causality Flag) | ✅ Implemented | `causality_claim: false` in all outputs. |
| **FR-009** (Validated Instruments) | ⚠️ Partial | Synthetic generator includes `validation_reference` field citing UKB papers. Real validation deferred. |
| **FR-010** (Over-Control) | ✅ Implemented | Reduced models. |
| **SC-001** (Retention Rate) | ⚠️ Synthetic | Measured against *synthetic* cohort size. Real rate deferred. |
| **SC-002** (FDR Rate) | ✅ Implemented | Measured on synthetic data. |
| **SC-003** (Power Script) | ⚠️ Synthetic | Validates *script logic* on injected effects. Real power analysis deferred. |
| **SC-004** (Interaction Sig) | ⚠️ Synthetic | Measured against injected interaction parameters. |
| **SC-005** (Sensitivity) | ⚠️ Synthetic | Measures code behavior on thresholds. |
| **SC-006** (Over-Control) | ⚠️ Synthetic | Measures model comparison logic. |

## Success Criteria (Reframed)

- **SC-001**: Synthetic Cohort Retention Rate is measured against the initial synthetic sample size.
- **SC-002**: Multiple-comparison error rate is measured against the Benjamini-Hochberg target on synthetic data.
- **SC-003**: Power analysis script is validated by detecting a known injected effect (beta=0.1) in the synthetic data.
- **SC-004**: Age-interaction effect significance is measured against the injected interaction parameters.
- **SC-005**: Sensitivity analysis measures how the *synthetic* headline rates vary across thresholds.
- **SC-006**: Over-control sensitivity measures the *synthetic* effect size variation between full and reduced models.

## Limitations

1.  **Biological Validity**: This study **cannot** validate the existence of a biological correlation between gut microbiome and cognition. It only validates the *pipeline*.
2.  **Statistical Power**: The power analysis is a code correctness test, not a true power analysis for real-world effects.
3.  **Confounding**: The synthetic confounding structure may not reflect the complexity of real UK Biobank data.
4.  **Data Access**: The project cannot proceed to the "Investigation" phase without access to real UK Biobank data.