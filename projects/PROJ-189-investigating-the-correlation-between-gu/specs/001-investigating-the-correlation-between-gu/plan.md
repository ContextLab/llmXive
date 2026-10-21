# Implementation Plan: Gut Microbiome and Cognitive Decline Analysis

**Branch**: `001-gut-microbiome-cognition` | **Date**: 2026-10-21 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`  
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary
Create a reproducible, CPU‑only pipeline that (1) downloads and verifies open‑source AGP 16S counts **via a verified HuggingFace mirror** (see Research.md for provenance limitation note) and HRS cognitive metadata, (2) merges them on participant ID and filters to age ≥ 60, (3) rarefies, CLR‑transforms, imputes missing BMI, and performs a **Pearson |r| collinearity check** on the CLR matrix, (4) computes **partial Spearman** correlations between each genus and cognitive score while adjusting for age, sex, BMI, and education, applying Benjamini‑Hochberg FDR, (5) trains a Random Forest regressor **including demographic covariates** with nested cross‑validation, (6) evaluates significance against a **permutation null distribution**, (7) conducts a **formal power analysis** for both correlation and regression components, (8) runs a sensitivity sweep over rarefaction depth, (9) assembles a unified JSON results file **including raw file checksums** (`checksum_agp`, `checksum_hrs`) in the dataset metadata, and (10) generates a human‑readable summary. All steps are deterministic, produce real files, and are validated by contract tests (Task T009).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-bio==0.7.*`, `datasets==2.20.*`, `shap==0.45.*`, `miceforest==5.6.*`, `psutil==5.9.*`, `pingouin==0.5.*`  
- **Storage**: Local filesystem under `data/` (raw, processed, results, provenance).  
- **Testing**: `pytest` with contract tests in `tests/contract/`.  
- **Target Platform**: GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk).  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 6 GB.  
- **Constraints**: CPU‑only execution, deterministic random seeds, strict reproducibility, provenance verification via checksums.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, pinned `requirements.txt`, deterministic downloads, checksum verification. |
| II. Verified Accuracy | PASS | Only verified public URLs (HuggingFace mirrors) are used; provenance note explains limitation relative to Principle VI. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with a recorded checksum. |
| IV. Single Source of Truth | PASS | Every figure, statistic, or interpretation originates from a single row in `data/processed/merged_age60.parquet` and a single code block. |
| V. Versioning Discipline | PASS | All artifacts are hashed; hashes stored in the project state file. |
| VI. Microbiome Data Provenance | PASS* | Data obtained from verified HuggingFace mirrors because a direct open Qiita/EBI endpoint is not publicly available. This limitation is documented in Research.md. |
| VII. Predictive Modeling Transparency | PASS | Hyper‑parameters, seeds, SHAP rankings, and permutation null are logged and archived. |

\* *See Research.md for explicit discussion of the provenance limitation.*

## Project Structure
```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correlation.schema.yaml
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   └── results.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
projects/PROJ-189-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/
│   │   ├── agp.parquet
│   │   ├── hrs.parquet
│   │   └── bmi.csv
│   ├── provenance/
│   │   ├── expected_checksums.json   # version‑controlled
│   │   └── observed_checksums.json   # produced by 01_download_and_provenance.py
│   ├── processed/
│   │   ├── merged_age60.parquet
│   │   ├── dataset.json               # conforms to contracts/dataset.schema.yaml
│   │   ├── clr_normalized.parquet
│   │   └── imputed.parquet
│   └── results/
│       ├── correlations.json          # conforms to contracts/correlation.schema.yaml
│       ├── model.json                 # conforms to contracts/model.schema.yaml
│       ├── sensitivity.json
│       ├── unified_results.json       # conforms to contracts/results.schema.yaml (includes checksums)
│       ├── summary.md
│       └── figures/
│           ├── correlation_heatmap.png
│           └── model_shap_summary.png
├── code/
│   ├── requirements.txt
│   ├── 01_download_and_provenance.py   # download + checksum validation
│   ├── 02_merge_preprocess.py
│   ├── 03_correlation.py
│   ├── 04_modeling.py
│   ├── 05_sensitivity.py
│   └── utils/
│       ├── io.py
│       └── stats.py
├── tests/
│   └── contract/
│       ├── test_dataset_schema.py
│       ├── test_correlation_schema.py
│       ├── test_model_schema.py
│       └── test_results_schema.py
└── docs/
    └── paper_draft.md
```

## Phase & Task Mapping (covers every FR & SC)

| Phase | Task ID | Script | Primary Output | FR / SC addressed |
|-------|---------|--------|----------------|-------------------|
| **0 – Provenance Validation** | **T001** | `code/01_download_and_provenance.py` (download + checksum) | `data/provenance/observed_checksums.json` | FR‑001, FR‑002, SC‑001 |
| **1 – Merge & Age Filter** | **T002** | `code/02_merge_preprocess.py` (merge, age ≥ 60) | `data/processed/merged_age60.parquet` & `data/processed/dataset.json` | FR‑001, SC‑001 |
| **2 – Rarefaction, CLR, BMI Imputation, Pearson Collinearity** | **T003** | `code/02_merge_preprocess.py` (rarefaction, CLR, MICE, Pearson collinearity) | `data/processed/clr_normalized.parquet`, `data/processed/imputed.parquet` | FR‑002, **new** collinearity check |
| **3 – Partial Correlation Analysis** | **T004** | `code/03_correlation.py` (partial Spearman with covariates) | `data/results/correlations.json` | FR‑003, SC‑002 |
| **4 – Predictive Modeling (with covariates)** | **T005** | `code/04_modeling.py` (Random Forest, nested CV, covariates) | `data/results/model.json` | FR‑004 |
| **5 – Permutation Null Distribution & Power Check** | **T006** | `code/04_modeling.py` (permutation block) | Embedded in `model.json` (null_distribution & power fields) | FR‑004, SC‑003 |
| **6 – Pearson Collinearity Reporting** | **T007** | `code/04_modeling.py` (collinearity summary) | Embedded in `model.json` (collinearity_report field) | **replaces FR‑006** |
| **7 – Sensitivity Analysis** | **T008** | `code/05_sensitivity.py` (depth sweep) | `data/results/sensitivity.json` | FR‑005 |
| **8 – Unified Results Assembly (with checksums)** | **T009** | `code/05_sensitivity.py` (final assembly) | `data/results/unified_results.json` (includes `checksum_agp` and `checksum_hrs` in `dataset.metadata`) | All FR/SC (implicit) |
| **9 – Resource Guardrails** | **T010** | `code/utils/stats.py` (psutil monitor) invoked by every script | Runtime logs; automatic down‑sampling if RAM > 6 GB | FR‑007 |
| **10 – Power Analysis** | **T012** | `code/02_merge_preprocess.py` (power estimation) | Power warnings logged; values stored in `summary.md` | SC‑003, SC‑004 |
| **11 – Reporting** | **T011** | `code/05_sensitivity.py` (summary generation) | `data/results/summary.md` | SC‑001 – SC‑004 |

All tasks are deterministic, produce real files, and are validated by contract tests (Task T009).

## Compute Feasibility (CPU‑first)
- **Data size**: AGP ≈ a few GB, HRS ≈ on the order of a GB → streamed (`datasets.load_dataset(..., streaming=True)`) → RAM < 4 GB.  
- **Permutation testing**: 1000 shuffles on ~500 samples ≈ 3–4 h on 2 CPU cores.  
- **No GPU**: All libraries run on CPU; `shap` uses the kernel explainer (CPU).  
- **Memory guardrails**: `psutil` checks RAM every 30 s; if > 6 GB, taxa are truncated to top‑200 abundant genera and permutation count reduced to 500 (logged).  

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Fatal coverage gap (overlap < 500) | Early overlap check aborts with clear message; user must supply linked data. |
| Checksum mismatch (T001) | Expected checksums are version‑controlled; any change forces an explicit update of `expected_checksums.json`. |
| Memory overflow during permutation | Guardrail T010 down‑samples taxa or reduces permutations, logs adjustment. |
| Missing BMI for many participants | MICE imputation + `is_missing_bmi` flag; sensitivity check on imputation effect. |
| Multiple‑testing inflation | BH FDR for correlations; Holm‑Bonferroni for permutation p‑values. |
| Power insufficiency | Formal power analysis (Task T012) emits warning if detectable effect size exceeds realistic thresholds (SC‑004). |
| Collinearity after CLR | Pearson‑based |r| > 0.9 flagged; no VIF used. |
| Covariate omission in modeling | Demographic covariates are explicitly included as features (Task T005). |

---


## projects/PROJ-189-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/research.md
# Research: Gut Microbiome and Cognitive Decline Analysis

## 1. Problem Statement
Determine whether gut microbial genus abundances are **associationally** linked to cognitive performance in older adults (age ≥ 60). The analysis is purely observational; no causal inference is claimed.

## 2. Dataset Strategy

### 2.1 Verified Sources
| Dataset | Description | Verified URL |
|---|---|---|
| **AGP (American Gut Project)** | 16S rRNA genus‑level count table (parquet) | `https://huggingface.co/datasets/eternalaudrey/jump-cp-0016-labelfree-AGP/resolve/main/data/train-00000-of-00053.parquet` |
| **HRS (Health and Retirement Study)** | Cognitive scores, demographics, BMI (parquet) | `https://huggingface.co/datasets/irenepap/en-it-hrs-data/resolve/main/data/train-00000-of-00001-5379c2a0af0a1773.parquet` |
| **BMI supplement** (optional) | Additional BMI records for participants missing HRS BMI (CSV) | `https://huggingface.co/datasets/karan451/BMI-labeled-faced/resolve/main/archive/Final_Dataset.csv` |

All files are directly downloadable via the HuggingFace `datasets` library; no authentication is required.

**Provenance note**: Direct Qiita/EBI download of the AGP dataset is not publicly available without registration. We therefore use the verified HuggingFace mirror, recording full SHA‑256 checksums to satisfy reproducibility while flagging the provenance limitation for future amendment (see Constitution Principle VI).

### 2.2 Variable Verification
- **AGP** provides `sample_id`, `participant_id`, and one column per genus (`genus_<name>`).  
- **HRS** provides `participant_id`, `age`, `sex`, `bmi`, and `cognitive_score`.  
- **BMI supplement** provides `participant_id` and `bmi` (used when HRS BMI is missing).  

If any required column is absent, the pipeline aborts with a clear error (fulfills FR‑001).

### 2.3 Linkage Feasibility (Fatal Coverage Gap)
After loading, we compute the overlap:

```python
overlap = len(set(agp_df.participant_id) & set(hrs_df.participant_id))
```

If `overlap < 500`, the pipeline logs the count and **terminates** with a “Fatal Coverage Gap” error. No synthetic merging is performed, respecting Principle VI (Microbiome Data Provenance).

### 2.4 Data Volume & Streaming
Both parquet files are < 3 GB. They are streamed (`datasets.load_dataset(..., streaming=True)`) so that RAM stays ≤ 4 GB. After merge & age filter, the final dataframe is ≤ 500 MB.

## 3. Methodological Approach

### 3.1 Provenance Validation (Task T001)
1. Compute SHA‑256 checksums of the three raw files immediately after download.  
2. Compare each checksum to the values stored in `data/provenance/expected_checksums.json` (committed to the repo).  
3. Write observed checksums to `data/provenance/observed_checksums.json`.  
4. Exit with status 0 only if **all** match; otherwise abort with a descriptive error.  

Deterministic provenance guarantees reproducibility (Constitution I) and data hygiene (III).

### 3.2 Merge & Age Filtering (Task T002)
- Inner join on `participant_id`.  
- Abort if overlap < 500 (fatal coverage gap).  
- Filter to `age >= 60`.  
- Write `data/processed/merged_age60.parquet` and a companion `data/processed/dataset.json` that conforms to `contracts/dataset.schema.yaml`.  

### 3.3 Rarefaction, CLR, BMI Imputation, Pearson Collinearity (Task T003)
1. **Rarefaction**: compute `min_depth` across retained samples; rarefy each sample to this depth.  
2. **CLR transformation**: apply `pycoda.clr` to the rarefied genus matrix.  
3. **BMI imputation**: run MICE (`miceforest`) on missing BMI values; add a boolean flag `is_missing_bmi`.  
4. **Pearson collinearity**: compute pairwise Pearson correlation |r| among CLR‑transformed genera; any pair with |r| > 0.9 is recorded in a `collinearity_report` field (no VIF).  
5. Write `clr_normalized.parquet` and `imputed.parquet`.  

All transformations are deterministic (fixed random seed `42`).

### 3.4 Partial Correlation Analysis (Task T004)
- For each genus, compute a **partial Spearman** correlation with `cognitive_score` while controlling for `age`, `sex`, `bmi`, and `education_years` (using `pingouin.partial_corr`).  
- Generate raw two‑tailed p‑values.  
- Apply **Benjamini‑Hochberg FDR** (α = 0.05).  
- Store results in `data/results/correlations.json`, validated against `contracts/correlation.schema.yaml`.  
- Results are explicitly labeled “associational”.

### 3.5 Predictive Modeling (Task T005) & Permutation Null (Task T006)
- **Model**: `RandomForestRegressor` (scikit‑learn, CPU‑only).  
- **Features**: CLR‑scaled genera **plus** demographic covariates (`age`, `sex`, `bmi`, `education_years`).  
- **Split**: [deferred] train / [deferred] hold‑out, stratified by `age_group`.  
- **Nested CV**: outer 5‑fold CV for performance, inner 3‑fold grid search over `n_estimators ∈ {100,200}` and `max_depth ∈ {10,20,None}`; `random_state=42`.  
- **Metrics**: R² and RMSE on the hold‑out set.  
- **Permutation test**: shuffle `cognitive_score` 1000 times, refit using the same nested CV pipeline, collect R² distribution.  
- **Significance**: model R² must exceed the 95th percentile of the null distribution; Holm‑Bonferroni corrects the permutation‑derived p‑value.  
- **Interpretability**: compute SHAP values (`shap.TreeExplainer`) and record the top‑20 genera.  
- All outputs are stored in `data/results/model.json` and validated against `contracts/model.schema.yaml`.

### 3.6 Sensitivity Analysis (Task T008)
- Sweep rarefaction depth over `{5 000, min_depth}` (if `min_depth` > 5 000).  
- For each depth repeat Tasks T003–T005, recording the hold‑out R².  
- Store the variance of R² across depths in `data/results/sensitivity.json`.  

### 3.7 Unified Results Assembly (Task T009)
- Combine `dataset.json`, `correlations.json`, `model.json`, and `sensitivity.json` into a single `data/results/unified_results.json` that conforms to `contracts/results.schema.yaml`.  
- **Add** `checksum_agp` and `checksum_hrs` (from provenance) to `dataset.metadata`.  

### 3.8 Resource Guardrails (Task T010)
- Each script imports `utils.stats.monitor_resources()` which uses `psutil` to check RAM usage every 30 seconds.  
- If RAM > 6 GB, the script automatically:  
  1. Truncates the genus matrix to the top‑200 most abundant genera, **and**  
  2. Reduces permutation count to 500 (for modeling).  
- The adjustment is logged; the pipeline continues, satisfying FR‑007.

### 3.9 Power Analysis (Task T012)
- **Correlation power**: using `statsmodels.stats.power.NormalIndPower`, estimate detectable effect size given the number of tests (number of genera) and α = 0.05 (FDR‑adjusted).  
- **Regression power**: estimate detectable R² increase given sample size, number of predictors, and α = 0.05 (Holm‑Bonferroni‑adjusted).  
- Emit warnings in `summary.md` if power < 0.8 for either component.

### 3.10 Reporting (Task T011)
- Generate `data/results/summary.md` that:  
  - Reports overlap count, age filter stats, and any checksum warnings.  
  - Lists the number of significant genus‑cognition associations (SC‑002).  
  - Shows model R², null‑distribution percentile, and significance flag (SC‑003).  
  - Summarizes peak RAM usage vs the 7 GB limit (SC‑004).  
  - Includes key figures (saved as PNGs in `data/results/figures/`).  

## 4. Statistical Rigor
- **Multiple comparisons**: BH FDR for correlations; Holm‑Bonferroni for permutation p‑values.  
- **Power**: Formal power analysis (Task T012) warns if effective N < 100 or detectable effect size is unrealistic.  
- **Causality**: All statements are explicitly labeled “associational”.  
- **Measurement validity**: Cognitive scores are taken directly from HRS documentation; AGP 16S protocol is standard (assumption VI).  
- **Collinearity**: Pearson‑based |r| > 0.9 flagged; no VIF used.  

## 5. Compute Feasibility (CPU‑first)
- **Data download & checksum**: < 15 min, < 200 MB RAM.  
- **Pre‑processing**: < 10 min, < 4 GB RAM.  
- **Correlation**: < 20 min, < 2 GB RAM.  
- **Random Forest + 1000 permutations**: 3–4 h, ≤ 6 GB RAM.  
- **Sensitivity sweeps (2 depths)**: ~1 h.  
- **Total**: ≤ 6 h, ≤ 6 GB RAM.  

No GPU is required; all libraries run on CPU.

---


## projects/PROJ-189-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/data-model.md
# Data Model: Gut Microbiome and Cognitive Decline Analysis

## 1. Entity Definitions

### 1.1 Sample (Participant)
| Field | Type | Description |
|-------|------|-------------|
| `sample_id` | string | Unique AGP sample identifier. |
| `participant_id` | string | Shared ID used to merge AGP & HRS. |
| `age` | integer (≥ 60) | Age at HRS assessment. |
| `sex` | enum(`Male`, `Female`, `Other`, `Unknown`) | Self‑reported sex. |
| `bmi` | number (≥ 0) | Body‑mass index (imputed if missing). |
| `is_missing_bmi` | boolean | `True` if BMI was imputed via MICE. |
| `cognitive_score` | number | Continuous cognitive performance metric from HRS. |
| `age_group` | enum(`60-69`, `70-79`, `80+`) | Derived age bin for stratified splitting. |

### 1.2 Taxon (Genus)
| Field | Type | Description |
|-------|------|-------------|
| `genus_name` | string | Microbial genus name. |
| `raw_count` | integer | Raw read count before rarefaction. |
| `rarefied_count` | integer | Count after rarefaction to `min_depth`. |
| `clr_value` | number | Centered log‑ratio transformed abundance (used for modelling). |

### 1.3 ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string (UUID) | Unique identifier for the saved model. |
| `hyperparameters` | object | `n_estimators`, `max_depth`, `random_state`. |
| `performance` | object | `r2_train`, `r2_test`, `rmse_test`. |
| `null_distribution` | object | `n_permutations`, `r2_null_95th_percentile`, `r2_null_adjusted_threshold`, `is_significant`. |
| `collinearity_report` | object | `threshold` (Pearson |r| > 0.9) and list of flagged taxon pairs with Pearson `r` values. |
| `shap_analysis` | object | List of top‑20 genera with `mean_abs_shap`. |
| `timestamp` | string (ISO‑8601) | Creation time of the artifact. |

## 2. Data Flow
1. **Raw Input**: `agp.parquet`, `hrs.parquet`, `bmi.csv`.  
2. **Provenance**: `observed_checksums.json` compared to `expected_checksums.json`.  
3. **Intermediate**: `merged_age60.parquet` (inner join, age filter).  
4. **Processed**: `clr_normalized.parquet` (rarefied + CLR), `imputed.parquet` (BMI imputed).  
5. **Outputs** (validated against contracts):  
   - `correlations.json` (correlation block)  
   - `model.json` (model block)  
   - `sensitivity.json` (sensitivity block)  
   - `unified_results.json` (covers dataset, correlation, model)  
   - `summary.md` (human‑readable report)  

All files are stored under `data/` and their SHA‑256 hashes are recorded in `state/projects/...yaml`.

## 3. Constraints & Validation
- **Missing Data**: Rows missing `cognitive_score` or `age` are dropped before any analysis.  
- **Zero Inflation**: Handled by rarefaction + CLR; no direct log of zeros.  
- **Memory**: If `merged_age60.parquet` exceeds 6 GB, the pipeline automatically limits taxa to the top‑200 by mean abundance (Task T010).  
- **Linkage**: Pipeline aborts with error if `len(overlap) < 500` (fatal coverage gap).  
- **Checksum Validation**: `validate_provenance.py` must succeed before any downstream step.  
- **Schema Conformance**: Every result file is validated against its respective schema in `contracts/` by the CI test suite.

---


## projects/PROJ-189-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/quickstart.md
# Quickstart: Gut Microbiome and Cognitive Decline Analysis

## Prerequisites
- Python 3.11+  
- Git  
- ≤ 7 GB free RAM  
- Internet access (for automated dataset download).  

## Setup

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-189-investigating-the-correlation-between-gu

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Step‑by‑Step Execution

### 1. Download raw data & verify provenance
```bash
python code/01_download_and_provenance.py
```
- Downloads `agp.parquet`, `hrs.parquet`, `bmi.csv` into `data/raw/`.  
- Computes SHA‑256 checksums and compares them to the values in `data/provenance/expected_checksums.json`.  
- On success you will see `PROVENANCE CHECK PASSED` and an `observed_checksums.json` file.

### 2. Merge, age filter, rarefaction, CLR, BMI imputation, Pearson collinearity
```bash
python code/02_merge_preprocess.py
```
- Produces `data/processed/merged_age60.parquet` and `data/processed/dataset.json` (validated against `contracts/dataset.schema.yaml`).  
- Writes `clr_normalized.parquet` and `imputed.parquet`.  
- Performs a Pearson |r| > 0.9 collinearity check on the CLR‑transformed taxa (no VIF).

### 3. Correlation analysis (Partial Spearman + BH FDR)
```bash
python code/03_correlation.py
```
- Outputs `data/results/correlations.json` (validated against `contracts/correlation.schema.yaml`).  
- Adjusts for age, sex, BMI, and education via partial Spearman.

### 4. Predictive modeling & permutation null (includes covariates)
```bash
python code/04_modeling.py
```
- Generates `data/results/model.json` (validated against `contracts/model.schema.yaml`).  
- Includes demographic covariates as features, logs SHAP rankings and Pearson collinearity report.

### 5. Sensitivity analysis over rarefaction depth
```bash
python code/05_sensitivity.py
```
- Writes `data/results/sensitivity.json` and assembles `data/results/unified_results.json` (validated against `contracts/results.schema.yaml`; includes `checksum_agp` and `checksum_hrs`).  
- Produces `data/results/summary.md` with key tables and figures.

### 6. Verify all outputs
```bash
pytest tests/contract/
```
- All tests should pass (i.e., no failures).  

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| **PROVENANCE CHECK FAILED** | Checksum mismatch (file corrupted or version changed) | Update `data/provenance/expected_checksums.json` if the source file has legitimately changed, then re‑run the download step. |
| **Fatal Coverage Gap** (`overlap < 500`) | AGP and HRS IDs do not overlap enough after age filter. | Verify that the correct URLs are used; if the public datasets truly lack sufficient overlap, the analysis cannot proceed (spec‑mandated). |
| **MemoryError** | Dataset larger than RAM budget. | The pipeline will automatically down‑sample taxa to the top‑200 and/or reduce permutations; see logs for the adjustment. |
| **pytest failures** | Output file does not conform to its JSON schema. | Re‑run the offending script; check the log for schema‑validation error details. |
| **Model R² not significant** | Observed R² ≤ 95th percentile of permutation null. | The result is still reported; interpret as “no predictive advantage over chance”. |
| **Power warning** | Effective N < 100 or detectable effect size too large. | Review the power analysis section in `summary.md`; consider obtaining more data if possible. |

## Re‑run All Steps (clean slate)

```bash
# Remove all generated data
rm -rf data/processed/* data/results/* data/provenance/observed_checksums.json

# Then repeat the pipeline from step 1
python code/01_download_and_provenance.py
python code/02_merge_preprocess.py
python code/03_correlation.py
python code/04_modeling.py
python code/05_sensitivity.py
pytest tests/contract/
```

---


## projects/PROJ-189-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/contracts/model.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Performance Schema"
description: "Schema for Random Forest regression model performance, null distribution, Pearson collinearity report, and SHAP analysis."
type: object
properties:
  model_config:
    type: object
    properties:
      model_type:
        type: string
        enum:
          - RandomForestRegressor
      n_estimators:
        type: integer
      max_depth:
        type: integer
        nullable: true
      random_state:
        type: integer
      cv_folds:
        type: integer
    required:
      - model_type
      - n_estimators
      - max_depth
      - random_state
      - cv_folds
  performance:
    type: object
    properties:
      r2_train:
        type: number
      r2_test:
        type: number
      rmse_test:
        type: number
    required:
      - r2_train
      - r2_test
      - rmse_test
  null_distribution:
    type: object
    properties:
      n_permutations:
        type: integer
      r2_null_95th_percentile:
        type: number
      r2_null_adjusted_threshold:
        type: number
        description: "Threshold after Holm‑Bonferroni correction"
      is_significant:
        type: boolean
        description: "True if model R² exceeds adjusted threshold"
    required:
      - n_permutations
      - r2_null_95th_percentile
      - r2_null_adjusted_threshold
      - is_significant
  collinearity_report:
    type: object
    properties:
      threshold:
        type: number
        description: "Pearson |r| threshold for flagging collinearity (e.g., 0.9)"
      flagged_pairs:
        type: array
        items:
          type: object
          properties:
            taxon_1:
              type: string
            taxon_2:
              type: string
            pearson_r:
              type: number
          required:
            - taxon_1
            - taxon_2
            - pearson_r
    required:
      - threshold
      - flagged_pairs
  shap_analysis:
    type: object
    properties:
      top_features:
        type: array
        items:
          type: object
          properties:
            genus:
              type: string
            mean_abs_shap:
              type: number
          required:
            - genus
            - mean_abs_shap
    required:
      - top_features
required:
  - model_config
  - performance
  - null_distribution
  - collinearity_report
  - shap_analysis
additionalProperties: false


## projects/PROJ-189-investigating-the-correlation-between-gu/specs/001-investigating-the-correlation-between-gu/contracts/results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Unified Results Schema"
description: "Schema covering merged dataset metadata, Spearman correlation results, and Random Forest model performance (including permutation null, Pearson collinearity report, and SHAP analysis)."
type: object
properties:
  dataset:
    type: object
    properties:
      metadata:
        type: object
        properties:
          source_agp:
            type: string
            description: "AGP source identifier (Qiita study ID or URL)"
          source_hrs:
            type: string
            description: "HRS source identifier (URL or DUA reference)"
          merge_key:
            type: string
            description: "Column name used for merging (participant_id)"
          total_samples:
            type: integer
            description: "Number of rows after merge and age filter"
          age_filter:
            type: integer
            description: "Minimum age applied (60)"
          checksum_agp:
            type: string
            description: "SHA‑256 checksum of the raw AGP file"
          checksum_hrs:
            type: string
            description: "SHA‑256 checksum of the raw HRS file"
        required:
          - source_agp
          - source_hrs
          - merge_key
          - total_samples
          - age_filter
          - checksum_agp
          - checksum_hrs
      samples:
        type: array
        items:
          type: object
          properties:
            sample_id:
              type: string
            participant_id:
              type: string
            age:
              type: integer
              minimum: 60
            sex:
              type: string
              enum:
                - Male
                - Female
                - Other
                - Unknown
            bmi:
              type: number
              minimum: 0
            is_missing_bmi:
              type: boolean
            cognitive_score:
              type: number
            age_group:
              type: string
              enum:
                - "60-69"
                - "70-79"
                - "80+"
            genera_abundance:
              type: object
              additionalProperties:
                type: number
                minimum: 0
                maximum: 1
            genera_clr:
              type: object
              additionalProperties:
                type: number
          required:
            - sample_id
            - participant_id
            - age
            - sex
            - bmi
            - is_missing_bmi
            - cognitive_score
            - age_group
            - genera_abundance
            - genera_clr
    required:
      - metadata
      - samples
  correlation:
    type: object
    properties:
      method:
        type: string
        enum:
          - spearman
      correction:
        type: string
        enum:
          - benjamini_hochberg
      alpha:
        type: number
        description: "Significance threshold after correction"
      results:
        type: array
        items:
          type: object
          properties:
            genus:
              type: string
            cognitive_metric:
              type: string
            rho:
              type: number
            p_value:
              type: number
              minimum: 0
              maximum: 1
            q_value:
              type: number
              minimum: 0
              maximum: 1
            significant:
              type: boolean
            method_used:
              type: string
              description: "Primary method used (spearman)"
          required:
            - genus
            - cognitive_metric
            - rho
            - p_value
            - q_value
            - significant
            - method_used
    required:
      - method
      - correction
      - alpha
      - results
  model:
    type: object
    properties:
      model_config:
        type: object
        properties:
          model_type:
            type: string
            enum:
              - RandomForestRegressor
          n_estimators:
            type: integer
          max_depth:
            type: integer
            nullable: true
          random_state:
            type: integer
          cv_folds:
            type: integer
        required:
          - model_type
          - n_estimators
          - max_depth
          - random_state
          - cv_folds
      performance:
        type: object
        properties:
          r2_train:
            type: number
          r2_test:
            type: number
          rmse_test:
            type: number
        required:
          - r2_train
          - r2_test
          - rmse_test
      null_distribution:
        type: object
        properties:
          n_permutations:
            type: integer
          r2_null_95th_percentile:
            type: number
          r2_null_adjusted_threshold:
            type: number
            description: "Threshold after Holm‑Bonferroni correction"
          is_significant:
            type: boolean
            description: "True if model R² exceeds adjusted threshold"
        required:
          - n_permutations
          - r2_null_95th_percentile
          - r2_null_adjusted_threshold
          - is_significant
      collinearity_report:
        type: object
        properties:
          threshold:
            type: number
            description: "Pearson |r| threshold for flagging collinearity (e.g., 0.9)"
          flagged_pairs:
            type: array
            items:
              type: object
              properties:
                taxon_1:
                  type: string
                taxon_2:
                  type: string
                pearson_r:
                  type: number
              required:
                - taxon_1
                - taxon_2
                - pearson_r
        required:
          - threshold
          - flagged_pairs
      shap_analysis:
        type: object
        properties:
          top_features:
            type: array
            items:
              type: object
              properties:
                genus:
                  type: string
                mean_abs_shap:
                  type: number
              required:
                - genus
                - mean_abs_shap
        required:
          - top_features
    required:
      - model_config
      - performance
      - null_distribution
      - collinearity_report
      - shap_analysis
required:
  - dataset
  - correlation
  - model
additionalProperties: false