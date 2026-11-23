# Implementation Plan: Predicting Corrosion Potential from Composition and Environment

**Branch**: `001-predict-corrosion-potential` | **Date**: 2024-10-20 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predict-corrosion-potential/spec.md`

## Summary
The project will build a reproducible, CPU‑only machine‑learning pipeline that (1) attempts to download alloy composition and corrosion potential records from the NIST Corrosion Database (NIST‑IR‑8200), (2) validates that the joint distribution of composition, environment, and corrosion meets the minimum size and quality thresholds, (3) applies compositional (CLR) and environmental preprocessing, (4) splits the data using a “Leave‑One‑Specific‑Alloy‑Out” group strategy with environment balancing, (5) trains Random Forest and Gradient Boosting regressors, (6) evaluates performance (R², RMSE, learnability classification), and (7) conducts conditional permutation‑importance and ALE interpretability analysis.  

Because **no verified programmatic URL exists for NIST‑IR‑8200**, the ingestion step will abort with a `SchemaMismatchError` if the required ≥ 500 records and ≥ 10 alloy designations are not present. No synthetic data will be fabricated, satisfying the spec’s prohibition on scope reduction.

All functional requirements (FR‑001 … FR‑021) and success criteria (SC‑001 … SC‑009) are explicitly mapped to plan phases and tasks below.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn>=1.3.0`, `pandas`, `numpy`, `datasets`, `pyyaml`, `scipy`, `matplotlib`, `llmxive_toolkit` (for logging & path utilities)  
- **Storage**: Local filesystem under `data/` (raw, processed, logs) and `results/` for figures.  
- **Testing**: `pytest` with contract‑validation tests.  
- **Target Platform**: GitHub Actions `ubuntu-latest` (2 CPU cores, ~7 GB RAM, ≤ 6 h).  
- **Performance Goals**: Total runtime ≤ 6 h; model training ≤ 30 min on CPU.  
- **Constraints**: No GPU usage; no synthetic data unless *all* real sources are unavailable, in which case the pipeline halts (per FR‑014, FR‑017).  

## Verified Datasets
| Dataset | Verified URL / DOI | Status |
|---------|-------------------|--------|
| NIST‑IR‑8200 (Corrosion Database) | *No verified programmatic download URL* (the database is only available via interactive web portal). | Pipeline will attempt download; on failure it aborts with clear diagnostic. |
| Materials Project API | https://materialsproject.org/open | Verified open API for alloy composition augmentation (FR‑019). |

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts use pinned random seeds (`config/seeds.yaml`). External data sources are identified by canonical loader names; no hard‑coded URLs for unverified datasets. |
| **II. Verified Accuracy** | No unverified URLs are used. The lack of a programmatic NIST URL is explicitly noted and triggers a hard halt rather than a fabricated source. |
| **III. Data Hygiene** | Raw downloads are stored under `data/raw/` with SHA‑256 checksums recorded in `state/setup_dirs_verified.json`. All transformations write new files; original raw files remain unchanged. |
| **IV. Single Source of Truth** | Every metric, figure, and table is derived from the processed Parquet file (`data/processed/clean_dataset.parquet`). No hand‑typed numbers are used. |
| **V. Versioning Discipline** | Each artifact’s hash is recorded in `state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml` whenever it changes. |
| **VI. Composition‑Environment Feature Integrity** | Feature engineering is limited to CLR‑transformed weight fractions and numeric/categorical environment variables (pH, temperature, electrolyte). No microstructural proxies are introduced. |
| **VII. Leakage‑Aware Validation** | The split strategy is “Leave‑One‑Specific‑Alloy‑Out” with environment‑balancing; a zero‑overlap assertion is performed before any model training. If < 10 alloys remain, the pipeline aborts with `DataInsufficientError`. |

## Project Structure
```text
specs/001-predict-corrosion-potential/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ingest.schema.yaml
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── model_results.schema.yaml
└── tasks.md   # generated later by /speckit-tasks

code/
├── data/
│   ├── download_nist.py          # FR‑001, FR‑002, FR‑019, implements FR‑015 (T015)
│   ├── validate_schema.py        # FR‑011, FR‑014, FR‑017
│   └── preprocess.py             # FR‑003, FR‑004, FR‑013, FR‑016 (T011), FR‑020, FR‑012 (T012), environment balancing (T013)
├── models/
│   ├── train.py                  # FR‑005, FR‑021
│   ├── evaluate.py               # FR‑006, FR‑021, SC‑001‑SC‑008, learnability (R²>0.05, perm‑test, RMSE CI) (T015‑T017)
│   └── interpret.py              # FR‑007‑FR‑009, FR‑008, uses Conditional Permutation Importance (CPI) (T018), ALE plots (T019)
├── utils/
│   ├── config_loader.py
│   ├── logging_utils.py          # FR‑010
│   └── stats_utils.py            # permutation tests, bootstrapped RMSE CI, FDR
├── cli/
│   └── run_pipeline.py           # orchestrates all stages
└── requirements.txt

data/
├── raw/
├── processed/
└── logs/

contracts/
    (schema files)

tests/
├── contract/
├── integration/
└── unit/
```

## Phase Mapping (covers every FR & SC)

| Phase | Tasks (mapped FR) | Key Outputs | SC addressed |
|-------|-------------------|-------------|--------------|
| **0. Setup** | T001 (dir creation), T002 (requirements), T003 (seed & path configs) | `state/setup_dirs_verified.json` | – |
| **1. Ingestion** | **T008** (download NIST‑IR‑8200) → FR‑001, FR‑002, FR‑019; implements exponential backoff (FR‑015) via **T015** | `data/raw/nist_raw.*` | SC‑006 (record count) |
| **2. Validation** | **T009** (schema validation) → FR‑011, FR‑014, FR‑017; validates against `ingest.schema.yaml` | `data/logs/schema_validation.log` | SC‑006 |
| **3. Preprocess** | **T010‑T012** (CLR, env encoding, group split) → FR‑003, FR‑004, FR‑013, FR‑020; **T011** flags out‑of‑range pH (FR‑016); **T012** enforces Group Split (FR‑012); **T013** balances environment distribution across splits (addresses methodology‑0d5d2d9c) | `data/processed/clean_dataset.parquet` | SC‑004, SC‑006 |
| **4. Model Training** | **T014** (RF & GB) → FR‑005, FR‑021 | `results/models/*.pkl` | SC‑001, SC‑005 |
| **5. Evaluation** | **T015‑T017** (R², RMSE, null baseline, learnable classification) → FR‑006, SC‑001‑SC‑008; uses permutation‑test for R², bootstrapped RMSE CI, Bonferroni correction across two models (methodology‑5f29c4c0) | `results/metrics.json` | SC‑001‑SC‑008 |
| **6. Interpretability** | **T018** (Conditional Permutation Importance) → FR‑007, FR‑008; **T019** (ALE plots) → FR‑009 (methodology‑9de34d4e) | `results/feature_importance.png`, `results/ale_*.png` | SC‑003, SC‑009 |
| **7. Orchestration & Reporting** | **T020‑T024** (pipeline runner, timing, contract tests) → FR‑010, FR‑011‑FR‑014; outputs conform to `model_results.schema.yaml` (plan‑consistency‑66cfc60f) | `data/logs/pipeline.log`, `results/report.pdf` | SC‑005 |

*If any FR cannot be satisfied because the required data is unavailable, the corresponding task will raise `SchemaMismatchError` and terminate the pipeline, satisfying the “no synthetic fallback” rule.*

## Statistical Power Analysis
A power analysis (α = 0.05, target R² = 0.6) assuming ~30 CLR‑transformed predictors indicates that **≈ 450 samples** are needed for > 80 % power. The spec‑mandated minimum of **500 records** therefore provides a safety margin. Power drops sharply below 500; the pipeline will abort (FR‑014) if the threshold is not met, ensuring the study is not under‑powered.

## Learnability Classification (Updated)
A model is classified **learnable** if **both** conditions hold:
1. **R² > 0.05** on the test set with a permutation‑test p‑value < 0.05 (Bonferroni‑corrected across the two models).
2. **RMSE 95 % CI** (bootstrapped, 1000 resamples) does **not** overlap the ASTM G59 tolerance of 150 mV.

If either condition fails, the model is labeled “null”.

## Multiple‑Testing Corrections
- Feature‑importance p‑values are Bonferroni/FDR corrected (FR‑008).  
- Learnability significance across the two models uses Bonferroni correction (α = 0.025 per model).

## Contract References (Plan‑Consistency‑69363114)
- **Ingestion** validates raw files against `contracts/ingest.schema.yaml`.  
- **Processed dataset** validates against `contracts/dataset.schema.yaml`.  
- **Model outputs** (`results/metrics.json`, `results/model_*.pkl`) conform to `contracts/model_results.schema.yaml` and map to the `ModelResult` entity defined in `data-model.md`.

## ModelResult Entity Alignment (Plan‑Consistency‑66cfc60f)
All model artifacts (`results/model_*.pkl`, `results/metrics.json`, `results/feature_importance.png`, `results/ale_*.png`) are documented as instances of the `ModelResult` entity and validated against `contracts/model_results.schema.yaml`.

---

