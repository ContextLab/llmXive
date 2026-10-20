# Implementation Plan: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Branch**: `001-the-influence-of-algorithmic-recommendations` | **Date**: 2026-10-19 | **Spec**: `spec.md`  
**Input**: Feature specification from `/specs/001-the-influence-of-algorithmic-recommendations/spec.md`

## Summary
The project will build a reproducible CPU‑only statistical pipeline that (1) ingests a public dataset containing recommendation‑type logs and enrollment‑type outcomes, (2) computes Shannon‑entropy‑based diversity scores for recommendations and subsequent enrollments, (3) derives a baseline interest vector for each learner, (4) applies **Generalized Propensity Score Weighting (GPSW)** to balance the continuous exposure (Recommendation Diversity) against baseline interests, (5) fits a weighted linear regression (or GLS fallback for N < 30), and (6) validates the effect with a residual permutation test and a semantic‑similarity‑threshold sensitivity sweep. All conclusions are framed as *associational*.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.19.*`, `sentence‑transformers==2.5.*` (for semantic similarity), `pyarrow==15.*`  
- **Storage**: Local filesystem under `data/` (raw, processed).  
- **Testing**: `pytest` (unit, integration, contract).  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤7 GB RAM, ≤6 h).  
- **Project Type**: Data‑analysis pipeline (CLI‑driven).  
- **Constraints**: CPU‑only; no causal claims; strict reproducibility; all external citations must be verified.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | `requirements.txt` pins exact versions; all random seeds are set in `code/config.py`; data files are checksummed; the pipeline can be rerun end‑to‑end on a fresh runner. |
| **II. Verified Accuracy** | All citations reference only the verified URLs listed in the “Verified datasets” block (e.g., the PSW parquet file). No invented sources. |
| **III. Data Hygiene** | Raw files are stored unchanged under `data/raw/` with SHA‑256 checksums recorded in the project state file; every transformation writes a new file under `data/processed/`. |
| **IV. Single Source of Truth** | Every figure/table in the final report is generated directly from `data/processed/` artifacts; no manual transcription. |
| **V. Versioning Discipline** | Content hashes of all artifacts are recorded; any change updates the `state/projects/...yaml` timestamp. |
| **VI. Causal Independence Validation** | Predictor (Recommendation Diversity) is derived from a *different* log (VLE or proxy) than the outcome (Enrollment Diversity); GPSW explicitly balances the continuous exposure against baseline interests. |
| **VII. Behavioral Agency Preservation** | The analysis treats a null result as publishable; language in the report is limited to “associated with” and never “causes”. |

## FR/SC Traceability Matrix
| ID | Requirement | Phase | Script/Module | Test |
|----|-------------|-------|----------------|------|
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
│   │   └── (verified parquet files)
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
| **0 – Data Fetch & Validation** | Acquire a verified open dataset and ensure required schema. | `code/data_fetcher.py` downloads the **PSW parquet** file (`https://huggingface.co/datasets/psw5495/pick_and_place/.../file-000.parquet`). Inspects columns; if `recommended_categories` and `enrolled_categories` are absent, maps existing columns (`input_seq`, `target_seq`) to the required names. Raises `DataSchemaError` if mapping fails. | `data/raw/validated_dataset.parquet` + checksum file |
| **1 – Preprocessing & Metric Calculation** | Build diversity scores, merge semantically similar categories, derive baseline vectors. | • Category merging via Sentence‑Transformers embeddings (cosine distance < configurable threshold).<br>• Shannon entropy (log₂) for both lists (FR‑001).<br>• Baseline vector from pre‑window rows (FR‑002).<br>• Log warnings for empty enrollment lists (US‑1). | `data/processed/cleaned_data.parquet`, `data/processed/diversity_scores.json`, `data/processed/baseline_vectors.parquet` |
| **2 – Modeling** | Estimate effect of recommendation diversity controlling for baseline interests. | • Fit **Generalized Propensity Score**: regress continuous diversity on baseline vector (Gaussian linear model) → compute density‑based weights (Stabilized).<br>• Weighted linear regression of Learner_Diversity on Recommendation_Diversity + Baseline (FR‑003).<br>• If unique users < 30 → GLS with robust SE (FR‑008).<br>• Compute VIF; flag if > 5 (SC‑004). | `data/processed/model_results.csv` |
| **3 – Robustness** | Validate effect and assess sensitivity. | • Residual permutation test (1,000 + shuffles) → null distribution, p‑value (FR‑004).<br>• Sensitivity sweep over thresholds {0.01, 0.05, 0.1} → table of coefficients/p‑values (FR‑005).<br>• Apply multiple‑comparison correction (Bonferroni) across the three thresholds. | `data/processed/permutation_test_results.json`, `data/processed/sensitivity_analysis.csv` |
| **4 – Reporting** | Produce final markdown report and ensure runtime budget. | `code/main.py` orchestrates all steps, measures wall‑clock time (SC‑005), writes `docs/reports/analysis_report.md` with associational language (FR‑006) and any warnings (e.g., extreme weights, sensitivity warnings). | `docs/reports/analysis_report.md` |

## Assumptions & Constraints
- **Dataset Availability**: The PSW parquet file is openly downloadable and will be repurposed; if its columns cannot be mapped to the required schema, the pipeline aborts with a clear `DataSchemaError`.  
- **Continuous Exposure Weighting**: GPSW (generalized propensity scores) is used, satisfying the reviewer’s concern about continuous treatments.  
- **Compute**: All steps are CPU‑friendly; semantic similarity uses a small pre‑downloaded sentence‑transformer (`all-MiniLM-L6-v2`).  
- **Missing Baseline**: Users lacking pre‑study history receive a uniform baseline vector; this is logged and flagged in the report.  
- **Small Sample**: GLS fallback ensures a valid analysis when N < 30 (FR‑008).  

---
