# Implementation Plan: Predicting Coating Adhesion Strength from Composition and Surface Features

**Branch**: `001-predicting-coating-adhesion` | **Date**: 2026-07-05 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-predicting-coating-adhesion/spec.md`

## Summary

This project implements a predictive modeling pipeline to determine the adhesion strength of coating-substrate pairs using compositional descriptors and surface metrology features. **CRITICAL STATUS**: The project is currently in a **Data Gap Analysis** state. The required verified dataset URLs for Materials Project API, NIST Surface Metrology Repository, and open-access literature sources are **missing or invalid** (current URLs point to medical data). Consequently, the proposed heuristic Mapping Protocol is **non-executable** and would introduce fatal scientific errors if run with mock data.

The plan below outlines the rigorous methodology to be executed **ONLY AFTER** verified data sources are provided. Until then, the pipeline will halt at Phase 1.1. The methodology includes:
1.  **Strict Data Alignment**: Rejection of any record pair not linked by a unique, verified identifier (eliminating heuristic mapping risks).
2.  **Construct Validity Assessment**: Validation of derived proxies (e.g., crosslinker density) against theoretical models before use.
3.  **Power Analysis & Stopping Rules**: Explicit halt if sample size < 1,000 to prevent Type II errors.
4.  **Rigorous Statistical Testing**: Nested CV, SHAP, permutation importance, and Nadeau & Bengio corrected t-tests with Bonferroni correction.
5.  **Resource Constraints**: All operations constrained to CPU-only execution on GitHub Actions free-tier (≤7 GB RAM, ≤6 h runtime).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `requests`, `numpy`, `pyyaml`  
**Storage**: Local CSV/JSON files (no external database; data cached in `data/` with checksums)  
**Testing**: `pytest` (unit tests for ingestion logic, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: Complete full pipeline (ingestion → modeling → reporting) within 4 hours to satisfy SC-004 (4h safety margin within 6h limit).  
**Constraints**: 
- No GPU/CUDA; all models must run in CPU mode.
- Memory cap: 7 GB (enforced via sampling to ≤5,000 records per FR-006).
- Runtime cap: A bounded duration (target 4h).
- No silent failures; all API errors (404, rate limits) must trigger explicit halts with logs.
- **Data Availability**: Pipeline halts if verified dataset URLs are not provided.
**Scale/Scope**: 
- Dataset: ≤5,000 rows (up from raw input).
- Models: Multiple primary (GB, RF) and baseline models.
- Features: ~ engineered descriptors.

> Note: Empirical dataset sizes and specific R² targets are deferred to `research.md` and `data-model.md` based on actual data availability and validation. **Current status: BLOCKED.**

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/` (e.g., `random_state=42`). External datasets fetched from canonical URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **FAIL** | **Remediation Required**: No verified URLs exist for required data sources. Current URLs point to medical data. Plan halts until valid sources are provided. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/` with checksums. Derivations written to `data/processed/` with new filenames. No PII allowed. |
| **IV. Single Source of Truth** | PASS | All figures/stats in `paper/` will trace to specific rows in `data/processed/` and code blocks in `code/`. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes. `state/` YAML updated on changes. |
| **VI. Computational Stability** | PASS | Models run in CPU-only mode. Nested CV used. Memory capped at 7 GB via sampling. Feature engineering validated for numerical stability. |
| **VII. Multi-Modal Rigor** | **FAIL** | **Remediation Required**: Multi-modal alignment (composition + surface) is impossible without verified unique identifiers. Current heuristic mapping is rejected. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-coating-adhesion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
data/
├── raw/                  # Raw downloads (checksummed)
│   ├── materials_project/
│   ├── nist_surface/
│   └── literature/
└── processed/            # Unified, cleaned datasets
    ├── coating_adhesion_dataset.csv
    └── logs/

code/
├── __init__.py
├── ingestion.py          # Data fetching & merging (FR-001, FR-007, FR-009)
├── preprocessing.py      # Feature engineering & imputation (FR-002, FR-006)
├── modeling.py           # Training, CV, SHAP (FR-003, FR-004)
├── evaluation.py         # Baseline comparison & stats (FR-005)
├── utils.py              # Logging, error handling, retry logic
└── main.py               # Orchestration script

tests/
├── unit/
│   ├── test_ingestion.py
│   ├── test_preprocessing.py
│   └── test_evaluation.py
└── integration/
    └── test_pipeline.py

requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead. All logic is contained within `code/` with clear separation of concerns (ingestion, preprocessing, modeling, evaluation). This aligns with the computational nature of the project and ensures reproducibility on CI.

## Complexity Tracking

No violations detected. The single-project structure is sufficient for the scope (≤5,000 rows, 2 models, 1 pipeline). **However, the project is currently blocked by missing data sources.**

## Implementation Phases

### Phase 0: Data Gap Analysis & Validation (BLOCKER)
- **Goal**: Verify availability of correct dataset URLs and assess alignment feasibility.
- **Steps**:
  1.  Verify URLs for Materials Project API, NIST Surface Metrology, and literature sources.
  2.  Confirm existence of unique identifiers or verified cross-references between sources.
  3.  **Halt** if URLs are invalid or unique identifiers are missing. Report "Data Gap" and do not proceed.
- **Success Criteria**: Valid URLs and unique identifiers confirmed.

### Phase 1: Data Ingestion & Engineering
- **Goal**: Ingest, clean, and engineer features from verified sources.
- **Steps**:
  1.  **1.1 Data Fetch & Validation**: Download raw data from verified sources. Validate checksums and schema.
  2.  **1.2 ASTM D4541 Filter & Validation (FR-009)**: Filter out all adhesion data not derived from ASTM D4541 pull-off tests. Log excluded records.
  3.  **1.3 Data Alignment Verification (FR-007)**: Attempt to align records using unique identifiers. **Reject** any pair that cannot be linked via a unique, verified identifier. Do not use heuristic mapping.
  4.  **1.4 Exclusion Ratio Validation (SC-005)**: Calculate the ratio of excluded records (due to missing targets or alignment failure) to total valid records. **Halt** if ratio ≥ 10%.
  5.  **1.5 Processing Success Rate Validation (SC-001)**: Calculate the percentage of valid records processed successfully. **Halt** if success rate < 95%.
  6.  **1.6 Power Analysis & Stopping Rule**: Perform formal power analysis. **Halt** if sample size < 1,000 (insufficient power for R² ≈ 0.6–0.7).
  7.  **1.7 Sensitivity Analysis on Crosslinker Density (FR-008)**: Test at least three different ratio-based definitions of 'crosslinker density'. Report variance in model performance.
  8.  **1.8 Construct Validity Assessment**: Validate derived proxies (e.g., crosslinker density) against theoretical models. **Exclude** any proxy that cannot be validated.
- **Success Criteria**: Clean, validated dataset with N ≥ 1,000, exclusion ratio < 10%, success rate ≥ 95%, and validated proxies.

### Phase 2: Predictive Modeling & Feature Importance
- **Goal**: Train models and rank features.
- **Steps**:
  1.  **2.1 Model Training**: Train Gradient Boosting and Random Forest Regressors with nested 5-fold cross-validation (FR-003).
  2.  **2.2 Feature Importance**: Compute SHAP values and permutation importance. Rank top 10 features (FR-004).
  3.  **2.3 Stability Check**: Verify Spearman correlation between SHAP and permutation importance rankings ≥ 0.8 (SC-003).
- **Success Criteria**: Non-empty ranked feature list, R² > -1, stability correlation ≥ 0.8.

### Phase 3: Statistical Comparison & Baseline Benchmarking
- **Goal**: Compare full-feature model against baselines.
- **Steps**:
  1.  **3.1 Baseline Training**: Train composition-only and surface-only baseline models.
  2.  **3.2 Statistical Testing**: Execute Nadeau & Bengio corrected t-test with Bonferroni correction (FR-005).
  3.  **3.3 Result Interpretation**: Determine if full model is significantly better (p < 0.05 after correction). Flag "Informative Null" if not (SC-002).
- **Success Criteria**: p-value < 0.05 (after correction) or explicit "Informative Null" flag.

### Phase 4: Reporting & Documentation
- **Goal**: Generate final reports and paper artifacts.
- **Steps**:
  1.  **4.1 Report Generation**: Compile model results, feature rankings, and statistical tests into JSON/Markdown.
  2.  **4.2 Paper Drafting**: Draft paper section, citing results from `data/processed/`.
  3.  **4.3 Validation**: Run final validation checks against contracts.
- **Success Criteria**: Complete report and paper draft.

## Risk Mitigation

1.  **Dataset Mismatch**: 
    - **Risk**: No verified URLs for required datasets.
    - **Mitigation**: **HALT** at Phase 0. Do not proceed with mock data.
2.  **API Rate Limits**: 
    - **Risk**: Materials Project API rate limiting.
    - **Mitigation**: Implement exponential backoff with a limited number of retries in `ingestion.py`.
3.  **Memory Overflow**: 
    - **Risk**: Raw data exceeds 7 GB.
    - **Mitigation**: Sample a subset of rows immediately after ingestion. Use chunked processing.
4.  **Runtime Exceedance**: 
    - **Risk**: SHAP or CV takes >6 hours.
    - **Mitigation**: Limit SHAP to a subset of the most influential features. Use fewer CV folds (if justified) or approximate SHAP.
5.  **Data Alignment Failure**: 
    - **Risk**: No unique identifiers between sources.
    - **Mitigation**: **REJECT** unmappable records. Do not use heuristic mapping. Report count of rejected records.

## Decision Rationale

- **Why Strict Rejection of Heuristic Mapping?** 
  - Heuristic mapping introduces spurious correlations and invalidates scientific claims. 
  - Unique identifiers are required for valid alignment.
- **Why Power Analysis & Stopping Rule?** 
  - Small sample sizes (<1,000) risk Type II errors. 
  - Explicit stopping rule prevents invalid conclusions.
- **Why Construct Validity Assessment?** 
  - Derived proxies must be validated to ensure they reflect physical reality.
- **Why Bonferroni Correction?** 
  - Multiple hypothesis tests (full vs. baselines) require correction to control family-wise error rate.

## References

- **Materials Project**: (No verified URL provided; must be sourced).
- **NIST Surface Metrology**: (No verified URL provided; must be sourced).
- **SHAP**: (No verified URL provided; library documentation assumed).
- **Nadeau & Bengio (2003)**: "Inference for the Generalization Error" (standard for CV comparisons).

**Note**: All dataset URLs in this document are placeholders. The actual implementation MUST use verified URLs from the project's `# Verified datasets` block. Currently, **no such URLs exist** for the required data sources, making this a blocking issue.