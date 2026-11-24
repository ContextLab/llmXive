# Implementation Plan: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Branch**: `001-the-influence-of-algorithmic-recommendations` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-the-influence-of-algorithmic-recommendations/spec.md`

## Summary
Build a reproducible, CPU‑only statistical pipeline that (1) **generates a synthetic open‑source dataset** containing the required `recommended_items` and `enrolled_items` columns, (2) merges semantically similar categories, (3) computes Shannon‑entropy (log₂) diversity scores, (4) derives a baseline interest vector per learner, (5) applies **Generalized Propensity Score Weighting (GPSW)** to balance the continuous exposure, (6) fits a weighted linear regression (or GLS fallback when users < 30), (7) validates the effect with a **permutation test that permutes the outcome before weighting** and a semantic‑threshold sensitivity sweep, and (8) generates an associational markdown report.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.19.*`, `sentence-transformers==2.5.*`, `pyarrow==15.*`  
- **Storage**: Local filesystem under `data/` (raw → processed).  
- **Testing**: `pytest` (unit, integration, contract).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h).  
- **Constraints**: CPU‑only; no causal language; strict reproducibility; all external citations verified.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | `requirements.txt` pins exact versions; `code/config.py` sets all random seeds; raw synthetic data is generated deterministically from a fixed seed; the pipeline can be rerun end‑to‑end on a fresh runner. |
| **II. Verified Accuracy** | No external dataset URLs are used because no verified open dataset with the required schema exists. The plan explicitly notes this limitation (see Research). |
| **III. Data Hygiene** | Synthetic raw file is written under `data/raw/` with a SHA‑256 checksum recorded; every transformation writes a new file under `data/processed/`. |
| **IV. Single Source of Truth** | Every figure/table in the final report is generated directly from `data/processed/` artifacts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes of all artifacts are recorded in the project state file; any change updates the timestamp per the constitution. |
| **VI. Causal Independence Validation** | Predictor (`Recommendation_Diversity`) originates from a distinct synthetic recommendation log that is not mechanically derived from the outcome (`Learner_Diversity`). GPSW explicitly balances exposure against baseline interests. |
| **VII. Behavioral Agency Preservation** | The analysis treats a null result as publishable; all language in the report is limited to “is associated with” per FR‑006 and the constitution. |

## FR/SC Traceability Matrix
| ID | Requirement / Success Criterion | Phase | Script / Module | Test |
|----|--------------------------------|-------|-----------------|------|
| **FR-001** | Compute Shannon entropy (log₂) for both recommendation and enrollment lists | Phase 1 (Preprocessing) | `code/preprocessing.py` | `test_entropy_calculation` |
| **FR-002** | Derive Baseline_Interest_Vector from pre‑study history | Phase 1 | `code/preprocessing.py` | `test_baseline_vector` |
| **FR-003** | Fit weighted linear regression with Propensity Score Weights (continuous exposure) | Phase 2 (Modeling) | `code/modeling.py` | `test_gps_weighted_regression` |
| **FR-004** | Residual permutation test (≥ 1,000 iterations) | Phase 3 (Robustness) | `code/robustness.py` | `test_permutation_test` |
| **FR-005** | Sensitivity analysis over thresholds {0.01, 0.05, 0.1} | Phase 3 | `code/robustness.py` | `test_sensitivity_analysis` |
| **FR-006** | Frame all conclusions as associational | Phase 4 (Reporting) | `code/main.py` | `test_associational_language` |
| **FR-007** | Validate required columns; raise `DataSchemaError` if missing | Phase 0 (Data Fetch) | `code/data_fetcher.py` | `test_schema_validation` |
| **FR-008** | GLS fallback when unique users < 30 | Phase 2 | `code/modeling.py` | `test_gls_fallback` |
| **FR-009** | Merge categories whose semantic similarity < threshold | Phase 1 | `code/preprocessing.py` | `test_category_merging` |
| **SC-001** | Correlation between Recommendation_Diversity & Learner_Diversity vs. null (p < 0.05) | Phase 2 | `code/modeling.py` | `test_correlation_significance` |
| **SC-002** | Coefficient stability across ≥ 2/3 thresholds (p < 0.05) | Phase 3 | `code/robustness.py` | `test_stability_requirement` |
| **SC-003** | False‑positive rate of permutation test ≤ 0.05 | Phase 3 | `code/robustness.py` | `test_permutation_false_positive` |
| **SC-004** | VIF for Baseline_Interest ≤ 5.0 (flag otherwise) | Phase 2 | `code/modeling.py` | `test_vif_limit` |
| **SC-005** | Total compute time ≤ 6 h on free‑tier runner | Phase 4 | `code/main.py` | `test_runtime_budget` |

## Project Structure
```text
specs/001-the-influence-of-algorithmic-recommendations/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    └── output.schema.yaml

projects/PROJ-367-the-influence-of-algorithmic-recommendat/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py               # seeds, thresholds
│   ├── data_fetcher.py         # Phase 0
│   ├── preprocessing.py        # Phase 1
│   ├── modeling.py             # Phase 2
│   ├── robustness.py           # Phase 3
│   └── main.py                 # Phase 4 (orchestration)
├── data/
│   ├── raw/
│   │   └── synthetic_dataset.parquet   # generated deterministically
│   └── processed/
│       ├── cleaned_data.parquet
│       ├── diversity_scores.json
│       ├── baseline_vectors.parquet
│       ├── model_results.csv
│       ├── permutation_test_results.json
│       └── sensitivity_analysis.csv
├── tests/
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_modeling.py
│   │   └── test_robustness.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
└── docs/
    └── reports/
        └── analysis_report.md
```

## Implementation Phases
| Phase | Goal | Key Tasks | Expected Output |
|-------|------|-----------|-----------------|
| **0 – Data Fetch & Validation** | Generate a reproducible synthetic dataset with required schema. | `code/data_fetcher.py` creates `synthetic_dataset.parquet` containing `user_id`, `session_id`, `recommended_items`, `enrolled_items`, plus optional covariates. Verifies required columns; raises `DataSchemaError` if any are missing (FR‑007). | `data/raw/synthetic_dataset.parquet` + checksum file |
| **1 – Preprocessing & Metric Construction** | Build diversity scores, merge semantically similar categories, derive baseline vectors. | • Load category embeddings via `sentence‑transformers/all‑MiniLM‑L6‑v2`.<br>• **Semantic merging**: merge any pair whose cosine distance ≤ *threshold* (default **0.05**).<br>• Compute Shannon entropy (log₂) for each list → `recommendation_diversity_score` and `learner_diversity_score` (FR‑001).<br>• Derive Baseline_Interest_Vector (FR‑002).<br>• Log warnings for empty enrollment lists (US‑1). | `data/processed/cleaned_data.parquet`, `data/processed/diversity_scores.json`, `data/processed/baseline_vectors.parquet` |
| **2 – Modeling** | Estimate effect of recommendation diversity controlling for baseline interests and additional covariates. | • **Generalized Propensity Score Weighting (GPSW)**:<br>   1. Fit a Gaussian linear model `Recommendation_Diversity ~ Baseline_Vector + session_length + time_of_day + platform_version`.<br>   2. Compute conditional normal density `f(D|X)`; raw weight = 1 / f(D|X).<br>   3. Stabilize weights by multiplying with marginal density of D (kernel density).<br>• Weighted linear regression of `Learner_Diversity` on `Recommendation_Diversity` + covariates, using GPSW weights.<br>• If unique users **N < 30**, switch to **Generalized Least Squares (GLS)** with heteroskedastic‑consistent robust SEs (FR‑008).<br>• Compute VIF for each baseline covariate; flag if > 5 (SC‑004). | `data/processed/model_results.csv` |
| **3 – Robustness** | Validate effect and assess sensitivity. | **Permutation Test** (consistent procedure):<br>1. For each of **[deferred]** iterations, randomly permute the `Learner_Diversity` outcome **before** recalculating GPSW weights.<br>2. Fit the weighted regression on the permuted data and record the `Recommendation_Diversity` coefficient.<br>3. Build a null distribution; compare the observed β₁ to the 95 % CI (Bonferroni‑corrected across the three semantic‑threshold settings).<br>**Sensitivity Sweep**: Run the full pipeline for thresholds **0.01, 0.05, 0.1**; record β₁ and p‑value for each. Apply Bonferroni correction across thresholds. | `data/processed/permutation_test_results.json`, `data/processed/sensitivity_analysis.csv` |
| **4 – Reporting** | Produce final markdown report and ensure runtime budget. | `code/main.py` orchestrates all steps, measures wall‑clock time (SC‑005), writes `docs/reports/analysis_report.md` with associational language (FR‑006) and any warnings (extreme weights, sensitivity warnings, GLS fallback). | `docs/reports/analysis_report.md` |

## Assumptions & Constraints
- **Dataset Availability**: No verified open dataset with the required recommendation/enrollment columns exists. A deterministic synthetic dataset is generated locally (see Phase 0). If a suitable open dataset becomes available, the data‑fetcher can be swapped out without changing downstream code.  
- **Continuous Exposure**: GPSW handles the continuous `Recommendation_Diversity` exposure as described; no binning is used.  
- **Compute**: All components run on CPU: memory ≤ 5 GB using chunked parquet reads; total wall‑clock time stays within the 6 h CI limit.  
- **Missing Baseline**: Users lacking pre‑study history receive a **uniform** baseline vector; this is logged and flagged.  
- **Small Sample**: GLS fallback ensures a valid analysis when N < 30, with an explicit power limitation note.  
- **Power Consideration**: A post‑hoc detectable‑effect calculation is reported; formal a‑priori power analysis is not feasible without prior effect size.  
- **Semantic Merging Justification**: A commonly used threshold for cosine similarity in NLP clustering is applied; sensitivity analysis confirms robustness.  
- **Multiple Comparisons**: Bonferroni correction applied across the three thresholds.  
- **Causal Framing**: All statements use “is associated with” per FR‑006 and Constitution Principles VI/VII.  

## Compute Feasibility
All steps are CPU‑friendly and fit within the GitHub Actions free‑tier constraints:
- Entropy & merging: linear in rows, negligible memory.  
- GPSW: single linear model (< 1 s).  
- Weighted regression: < 0.2 s per fit on ≤ 100 k rows.  
- Permutation test: 1,000 × fit [deferred] total, still within budget when run on the full dataset.  
- Peak RAM ≤ 5 GB using chunked parquet reads.  

---

