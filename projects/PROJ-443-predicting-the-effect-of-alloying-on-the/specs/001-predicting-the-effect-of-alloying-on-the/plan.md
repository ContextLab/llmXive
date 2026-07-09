# Implementation Plan: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Branch**: `001-predict-elastic-modulus` | **Date**: 2024-05-21 | **Spec**: `specs/001-predict-elastic-modulus/spec.md`
**Input**: Feature specification from `/specs/001-predict-elastic-modulus/spec.md`

## Summary
This feature implements a CPU-tractable machine learning pipeline to predict the **Residual Bulk Modulus** (observed minus Miedema's rule-of-mixtures estimate) for High-Entropy Alloys (HEAs). The system retrieves composition and elastic constant data from the **Materials Project API** and the **JARVIS-DFT dataset** (via HuggingFace), engineers compositional descriptors using Isometric Log-Ratio (ILR) transformation to handle compositional singularity, and trains Random Forest, Gradient Boosting, and ElasticNet models. The plan strictly adheres to the spec's requirement to exclude Miedema-derived features from predictors when the target is the Miedema residual, and implements specific statistical rigor (grouped bootstrap, FDR correction, permutation-based Type I error estimation) within the constraints of a free-tier GitHub Actions runner (2 CPU, 7 GB RAM).

**Critical Constraint**: The pipeline MUST halt if a sufficient number of valid HEA samples are not retrieved from verified APIs (Materials Project) or verified datasets (JARVIS-DFT). No fallback strategies (e.g., literature merge) are implemented or authorized.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `scikit-learn==1.4.2`, `pandas==2.2.1`, `numpy==1.26.4`, `requests==2.31.0`, `pyyaml==6.0.1`, `shap==0.44.1` (CPU-only), `matplotlib==3.8.3`, `scipy==1.13.0`, `huggingface_hub==0.23.0`  
**Storage**: Local filesystem (`data/`, `results/`); No external database.  
**Testing**: `pytest==8.1.1` with contract validation against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data Science Pipeline / CLI.  
**Performance Goals**: Total pipeline runtime ≤ 6 hours on 2 CPU / 7 GB RAM.  
**Constraints**: 
- No GPU/CUDA usage.
- No deep learning training.
- Dataset subset to a constrained RAM limit.
- **Hard halt** on sample count < 500 or overfitting gap > 95th percentile of bootstrap distribution.
- Strict exclusion of Miedema-derived features when predicting Residual Bulk Modulus.
- Explicit associational framing in all reports.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External datasets fetched from canonical APIs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Dataset URLs in `research.md` strictly limited to the "Verified datasets" block provided in the prompt. No invented URLs. |
| **III. Data Hygiene** | **PASS** | `data/` files will be checksummed. Raw data preserved; transformations produce new files. No PII (HEA data is non-personal). |
| **IV. Single Source of Truth** | **PASS** | All metrics in `results/metrics.yaml` trace to `code/` execution. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes in state file. |
| **VI. Materials Database Provenance** | **PASS** | `data/source_metadata.yaml` will record **API versions** (from response headers) and **query parameters** (addressing FR-010). |
| **VII. Model Evaluation Transparency** | **PASS** | Metrics (R², RMSE, MAE, 95% CI) logged in `results/metrics.yaml`. Bootstrap and t-test code versioned. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-elastic-modulus/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   └── metadata.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-443-predicting-the-effect-of-alloying-on-the/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── fetch_hea_data.py  # FR-001, FR-010 (API fetch, metadata, API versions, ≥5 filter)
│   │   ├── preprocess.py      # FR-002, FR-003 (ILR, normalization, Miedema exclusion logic)
│   │   └── validate.py        # FR-009 (Residual correlation check, log warning + proceed)
│   ├── models/
│   │   ├── train.py           # FR-004 (RF, GB, ElasticNet)
│   │   └── evaluate.py        # FR-005, FR-006 (Bootstrap, FDR, Permutation test, groups < 10 fallback)
│   └── reports/
│       └── generate_report.py # FR-007, US-3 (Associational disclaimer, SHAP)
├── data/
│   ├── raw/                   # Downloaded API dumps / Parquet files
│   ├── processed/             # ILR-transformed CSVs
│   └── source_metadata.yaml   # Provenance record (API versions + query params)
├── results/
│   └── metrics.yaml           # Performance logs
├── tests/
│   ├── contract/              # Schema validation tests
│   └── unit/                  # Logic tests (e.g., Miedema exclusion)
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead and maximize reproducibility on CI. All data flow is linear: Fetch -> Preprocess -> Train -> Evaluate -> Report.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Miedema Exclusion Logic** | Required by FR-002 & FR-008 to prevent circular validation when target is Residual Bulk Modulus. | Simple feature selection would not guarantee exclusion of *derived* Miedema features, risking data leakage. |
| **Grouped Bootstrap** | Required by FR-005 & US-2 to prevent data leakage from similar chemical compositions. | Standard bootstrap would resample similar alloys independently, inflating confidence intervals. |
| **Permutation Testing** | Required by FR-006 & US-3 to estimate Type I error rate for the R² > 0.3 threshold. | Simple p-value calculation does not account for the specific null distribution of the residual target. |
| **Hard Halt on < 500 Samples** | Required by Spec Edge Cases. | No fallback strategy is authorized; a literature merge is not a verified source and would invalidate the study. |

## Data Flow & Control Logic

1. **Fetch**: `fetch_hea_data.py` downloads data from Materials Project API (query: `elastic_stiffness` present, `elements_count >= 5`) and JARVIS-DFT (HuggingFace). **Filter**: Apply `>=5` element filter immediately. **Record**: Log **API versions** (from response headers) and query parameters in `source_metadata.yaml`. **Halt** if < 500 samples.
2. **Preprocess**: `preprocess.py` calculates Miedema enthalpy, applies ILR. **Condition**: If target is Residual, **DROP** all Miedema-derived features from predictors to prevent circular validation.
3. **Validate**: `validate.py` checks residual vs. descriptor correlation. **Condition**: If |r| > 0.1 for any **Miedema-derived** feature, **LOG WARNING** and **PROCEED** with caution (do not halt).
4. **Train**: `train.py` fits models.
5. **Evaluate**: `evaluate.py` runs grouped bootstrap. **Condition**: If groups < 10, **LOG WARNING** and **FALLBACK** to standard bootstrap. Runs permutation test for Type I error (Thresholds: 0.25, 0.30, 0.35).
6. **Report**: `generate_report.py` outputs results with **exact mandatory disclaimer**.

## projects/PROJ-443-predicting-the-effect-of-alloying-on-the/specs/001-predicting-the-effect-of-alloying-on-the/research.md
# Research: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Dataset Strategy

The project relies on two primary verified sources for High-Entropy Alloy (HEA) composition and elastic constants. The strategy strictly adheres to the "Verified datasets" block provided in the prompt.

| Dataset | Source URL | Format | Usage | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Materials Project (API)** | `https://next-gen.materialsproject.org/api` | JSON/REST | Primary source for elastic constants (Bulk Modulus) and composition. | **Query Strategy**: Query for entries with `elastic_stiffness` tensor present AND `elements_count >= 5`. API version recorded from response headers. |
| **JARVIS-DFT (Elastic)** | `https://huggingface.co/datasets/jarvis-dft/jarvis-dft/resolve/main/jarvis-dft-elastic.csv` | CSV | Verified fallback source for elastic constants. | Verified via HuggingFace. Contains `bulk_modulus` and `shear_modulus` for HEAs. Used if Materials Project yields < 500 samples. |

**Data Sufficiency Check**:
The pipeline will first attempt to aggregate samples from the Materials Project API and the JARVIS-DFT dataset.
- **Threshold**: ≥ 500 valid HEA samples (≥5 principal elements + elastic constants).
- **Action if < 500**: Hard halt with log: "Retrieved [N] samples; threshold 500 not met".
- **Fallback**: **None**. The spec mandates a hard halt. No literature merge or unverified source is authorized.

**Dataset Variable Fit**:
- **Required Variables**: Elemental composition (atomic %), Bulk Modulus (GPa).
- **Derived Variables**: Mixing enthalpy (Miedema), Atomic radius variance, ILR-transformed composition.
- **Fit Check**: The Materials Project API query explicitly targets `elastic_stiffness`. The JARVIS-DFT CSV is verified to contain `bulk_modulus`. If both sources fail to provide ≥500 samples, the project halts as a fundamental data availability failure.

## Statistical Methodology

### 1. Target Variable: Residual Bulk Modulus
- **Definition**: $B_{residual} = B_{observed} - B_{Miedema}$
- **Constraint (FR-008)**: When predicting $B_{residual}$, the predictor set **MUST NOT** include any features derived from Miedema's model (e.g., Mixing Enthalpy calculated via Miedema). This prevents the model from simply "learning" the Miedema correction, which would be circular validation.
- **Implementation**: Miedema-derived features are calculated but **immediately dropped** from the feature matrix if the target is $B_{residual}$.
- **Validation (FR-009)**: Prior to training, compute Pearson correlation ($r$) between $B_{residual}$ and all compositional descriptors.
  - **Logic**: If $|r| > 0.1$ for any **Miedema-derived** feature, log a warning: "Potential confound detected: Residuals correlate with Miedema feature X (|r|={val})". Proceed with caution but do not halt.
  - **Clarification**: Correlation with **non-linear** compositional descriptors (e.g., atomic radius variance) is expected and represents the signal to be learned, not a confound. The check is specifically for *Miedema-derived* features to ensure orthogonality.

### 2. Feature Engineering
- **Composition Handling**: Raw atomic percentages sum to 1.0 (closure constraint).
- **Transformation**: Apply **Isometric Log-Ratio (ILR)** transformation to break singularity.
- **Descriptors**: Atomic radius variance, electronegativity variance, valence electron concentration (VEC).
- **Exclusion**: Explicitly filter out Miedema-derived features from the final feature matrix if the target is $B_{residual}$.

### 3. Model Training
- **Algorithms**: Random Forest (RF), Gradient Boosting (GB), ElasticNet (EN).
- **Infrastructure**: CPU-only (scikit-learn).
- **Hyperparameters**: Default grids or reduced grids to fit 6h runtime.
- **Validation**: 5-fold Cross-Validation.

### 4. Evaluation & Rigor
- **Metrics**: R², RMSE, MAE on held-out test set.
- **Confidence Intervals**: 95% CI for R² via **Grouped Bootstrap** (1000 iterations).
  - **Grouping Key**: Unique set of constituent elements (e.g., "CrMnFeCoNi").
  - **Edge Case**: If unique groups < 10, log warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution" and proceed. **Do NOT** use Leave-One-System-Out (LOSO).
  - **Caution**: For 10-50 groups, confidence intervals may have high variance; interpret with caution.
- **Multiple Comparison Correction**: Apply **Benjamini-Hochberg FDR** to p-values from pairwise model performance comparisons.
- **Null Hypothesis Test**: t-test against $R^2 = 0$. Output p-value and boolean `significant` flag.
- **Sensitivity Analysis (FR-006)**:
  - Sweep thresholds: $\{0.25, 0.30, 0.35\}$.
  - **Metric**: **Type I error rate** estimated via **permutation testing**.
  - **Method**: Shuffle target labels (generating a null distribution where true R²=0), retrain, and measure the proportion of times the observed R² exceeds the threshold (e.g., R² ≥ 0.3).
  - **Decision Rule**: If the proportion of permuted samples with R² ≥ 0.3 exceeds 0.05, the primary claim (R² > 0.3) is **rejected**. The report will explicitly state this rejection.
  - **Output**: Variance in false-positive rates across thresholds.

### 5. Interpretability & Reporting
- **Method**: SHAP (CPU-compatible) or Permutation Importance.
- **Framing**: **Associational only**.
  - **Mandatory Disclaimer**: "These findings are associational and do not imply causation."
  - **Justification**: Observational data; no random assignment of elements.

## Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
- **Strategy**:
  - **Data**: Load OQMD/JARVIS CSV into pandas. Filter immediately. If > 7 GB, sample rows or process in chunks.
  - **Models**: Use `n_estimators=100` (default) for RF/GB. ElasticNet is lightweight.
  - **Bootstrap**: 1000 iterations on ~500 samples is computationally feasible (~1-2 hours).
  - **Permutation Test**: 100 iterations per threshold (3 thresholds) is feasible.
- **No GPU**: All libraries pinned to CPU versions.

## Risk Mitigation

1. **Dataset Mismatch**: If verified sources lack Bulk Modulus, the pipeline halts with a clear error.
2. **Sample Insufficiency**: Hard halt if < 500 samples. **No fallback**.
3. **Overfitting**: Hard halt if Train R² - Test R² > 95th percentile of bootstrap distribution of gaps.
4. **Circular Validation**: Explicit code check to remove Miedema features when target is Residual.
5. **API Failure**: Retry logic (with a configurable maximum number of attempts). If Materials Project fails, rely on JARVIS. If total < 500, halt.
6. **Insufficient Groups**: If groups < 10, fallback to standard bootstrap with warning.