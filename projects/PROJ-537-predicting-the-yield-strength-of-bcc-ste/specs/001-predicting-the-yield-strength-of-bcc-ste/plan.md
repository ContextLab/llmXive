# Implementation Plan: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Branch**: `001-predict-yield-strength-bcc` | **Date**: 2023-10-27 | **Spec**: `specs/001-predicting-the-yield-strength-of-bcc-ste/spec.md`

## Summary

This project implements a machine learning pipeline to predict the macroscopic yield strength of Body-Centered Cubic (BCC) iron alloys using a combination of chemical composition features and atomic-scale descriptors derived from Density Functional Theory (DFT). The approach involves merging experimental yield strength data from verified public repositories (MatNavi/NIST proxies) with pre-computed DFT elastic constants (bulk and shear modulus) from the Materials Project dataset (hosted on HuggingFace). A Random Forest regressor will be trained and compared against a composition-only baseline to quantify the added predictive value of physics-based descriptors.

**Critical Methodological Constraint**: This project **strictly prohibits the use of synthetic/mock data** for the core analysis. The research question ("Do DFT descriptors improve prediction?") requires empirical validation. If the verified real-world datasets do not contain sufficient overlap of BCC Fe-alloys (n < 20), the study will **not** fabricate data. Instead, it will report a "Data Availability Failure" (if n=0) or proceed in "Exploratory Mode" (if 0 < n < 20), focusing on effect sizes and confidence intervals without making statistical significance claims (omitting the paired t-test).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `numpy`, `matplotlib`, `seaborn`, `shap`, `datasets` (HuggingFace), `pytest`  
**Storage**: Local CSV/Parquet files in `data/` (raw and processed); JSONL logs in `data/provenance/`; `state.json` for versioning.  
**Testing**: `pytest` (unit tests for data merging, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (data fetch -> merge -> train -> evaluate) within 6 hours on free-tier CPU.  
**Constraints**: No GPU usage; no on-the-fly DFT calculations; memory usage < 7 GB; strict adherence to verified dataset sources.  
**Scale/Scope**: Merged dataset expected < 1000 rows (small sample size necessitates careful cross-validation and effect-size reporting).

## Constitution Check

- **I. Reproducibility**: All random seeds (`np.random.seed`, `random.seed`) will be pinned in `code/`. Data fetch scripts will log checksums of the downloaded datasets. The **content hash of the data ingestion and processing scripts** (`fetch_experimental.py`, `merge.py`) will be recorded in the `state.json` file as the canonical source for data derivation, ensuring the transformation logic is reproducible.
- **II. Verified Accuracy**: All data sources are cited by their verified HuggingFace URLs. The `research.md` will explicitly record the dataset version and hash. No synthetic data is used for the primary analysis.
- **III. Data Hygiene**: Raw data (downloaded from HuggingFace) will be checksummed. All transformations (merge, filter) will produce new files with derivation logs.
- **IV. Single Source of Truth**: All figures and statistics will be generated programmatically from `data/` artifacts.
- **V. Versioning**: `requirements.txt` will pin versions. The content hash of the downloaded datasets and the **content hash of the data processing code** will be recorded in `state.json`.
- **VI. Statistical Significance Transparency**: All hypothesis tests (paired t-test, Pearson correlation) will report null hypotheses, test statistics, and p-values **only if n >= 20**. If n < 20, the plan will omit p-values and report effect sizes (Cohen's d) and confidence intervals, explicitly acknowledging the lack of power.
- **VII. DFT Descriptor Provenance**: The source of DFT descriptors is the `materialsproject/elasticity` dataset on HuggingFace. A provenance log will record the dataset version, query parameters, and the specific material IDs used. **Synthetic data is explicitly prohibited** to satisfy this principle.

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-yield-strength-bcc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── state.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/code/
├── __init__.py
├── config.py            # Paths, seeds, thresholds
├── data/
│   ├── __init__.py
│   ├── fetch_experimental.py   # FR-001: Fetch/Load NIST/MatNavi data (Real Verified Proxy)
│   ├── fetch_dft.py            # FR-002: Fetch/Load DFT data (Materials Project via HuggingFace)
│   ├── merge.py                # FR-003: Merge & Filter
│   └── preprocessing.py        # Feature engineering
├── models/
│   ├── __init__.py
│   ├── train.py                # FR-004: Train RF
│   ├── evaluate.py             # FR-005, SC-001, SC-002, SC-003
│   ├── shap_analysis.py        # FR-006: SHAP values
│   └── sensitivity.py          # FR-007, FR-008
├── utils/
│   ├── logging.py
│   └── stats.py                # T-tests, bootstrapping, power analysis
└── main.py                     # Pipeline orchestrator

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: A modular Python package structure is chosen to separate data ingestion, modeling, and evaluation. This supports the "Reproducibility" principle by isolating side effects (data fetch) in `data/` and ensuring `models/` are pure functions of inputs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Verified Real Data | Synthetic data violates scientific soundness and Constitution Principle VII. | Using synthetic data creates a circular validation where the answer is pre-determined by the generator. |
| 5-Fold CV + Bootstrapping | Required by FR-005 and FR-008 for statistical rigor on small datasets. | Single train/test split would violate the statistical significance transparency principle (VI) and fail the sample size robustness checks. |
| SHAP Analysis | Required by FR-006 for interpretability. | Permutation importance alone is insufficient for detailed feature contribution analysis in complex models. |
| Conditional Statistical Testing | Required to maintain rigor when n < 20. | Performing a t-test on 5 fold-wise pairs (n=5) is statistically invalid. The plan now omits the t-test if n < 20. |

## Phase Breakdown

### Phase 1: Data Ingestion & Validation (FR-001, FR-002, FR-003)
1. **Fetch Experimental Data**: Load experimental yield strength data from verified NIST/MatNavi sources (or a verified proxy dataset on HuggingFace). **FR-001**.
2. **Fetch DFT Data**: Load DFT elastic constants from `materialsproject/elasticity` on HuggingFace. **FR-002**.
3. **Merge & Filter**: Join on chemical formula. Filter for BCC structure (Space Group corresponding to the body-centered cubic lattice). **FR-003**.
4. **Validation**: Check sample size.
   - If n = 0: Raise `DataAvailabilityError` and terminate.
   - If 0 < n < 20: Log `PowerWarning`, switch to "Exploratory Mode" (report effect sizes, omit p-values).
   - If n >= 20: Proceed with full statistical testing.

### Phase 2: Feature Engineering & Modeling (FR-004, FR-005)
1. **Feature Engineering**: Create composition features (one-hot, atomic fractions) and DFT features (shear, bulk, Pugh's ratio).
2. **Model Training**: Train Random Forest (with DFT) and Baseline (composition only) using k-fold cross-validation.
3. **Evaluation**: Calculate R², MAE, and RMSE for each fold.
4. **Statistical Testing**:
   - **Pearson Correlation**: Calculate r and p-value (or CI) between `shear_modulus` and `yield_strength` (SC-001).
   - **Significance Test**: If n >= 20, perform paired t-test on fold-wise errors. If n < 20, calculate and report Cohen's d and 95% CI for the difference in MAE, explicitly stating that p-values are invalid.

### Phase 3: Interpretability & Sensitivity (FR-006, FR-007, FR-008)
1. **SHAP Analysis**: Generate SHAP values to quantify feature contributions (FR-006). **Explicitly implemented in `shap_analysis.py`**.
2. **Sensitivity Analysis**: Sweep DFT threshold and report MAE/R² variation (FR-007).
3. **Stability Analysis**: Bootstrap 10 samples to calculate standard deviation of importance scores (FR-008).

### Phase 4: Reporting
1. **Generate Reports**: Compile all metrics, plots, and statistical tests into `data/processed/model_results.json`.
2. **Constitution Check**: Verify all results trace back to `data/` and `code/`. Record content hashes in `state.json`.

## Success Criteria (Revised)

- **SC-001**: Report Pearson correlation (r) between `shear_modulus` and `yield_strength` with 95% confidence interval. (Target: r > 0.5, but report actual value).
- **SC-002**: Report MAE difference between DFT model and Baseline with a confidence interval.
- **SC-003**: Report p-value from paired t-test **only if n >= 20**. If n < 20, report Cohen's d and 95% CI.
- **SC-004**: Report variation in MAE/R² across sensitivity sweep.
- **SC-005**: Report standard deviation of SHAP importance scores across bootstraps.
