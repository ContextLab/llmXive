# Implementation Plan: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Branch**: `001-gene-regulation` | **Date**: 2026-06-28 | **Spec**: `specs/001-quantifying-the-effect-of-alloying-eleme/spec.md`
**Input**: Feature specification from `specs/001-quantifying-the-effect-of-alloying-eleme/spec.md`

## Summary

This project implements a computational pipeline to quantify the effect of alloying elements on the Glass-Forming Ability (GFA) of metallic glasses. The system ingests experimental data, engineers physics-based descriptors using Pymatgen, trains Random Forest and Gradient Boosting regression models to predict the logarithm of the critical cooling rate ($log_{10}(R_c)$), and screens novel ternary compositions. The pipeline includes rigorous validation (LOCO cross-validation), uncertainty quantification (bootstrapping, Domain of Applicability), and novelty checking, all designed to run on CPU-only GitHub Actions runners.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `shap`, `statsmodels`, `scipy`
**Storage**: Local file system (CSV, JSON, Pickle artifacts); `state/` directory for artifact hashes (Constitution Principle V)
**State Management**: `state/` directory for artifact hashes and versioning (Constitution Principle V)
**Testing**: `pytest` (unit, integration, contract)
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)
**Project Type**: Data Science Pipeline / CLI
**Performance Goals**: Complete pipeline execution ≤ 6 hours on CPU-only runner; Memory usage < 7GB.
**Constraints**: No GPU/CUDA; No large-LLM inference; Deterministic random seeds; CPU-tractable combinatorial generation.
**Scale/Scope**: [deferred] of experimental compositions; [deferred] unique ternary combinations (30 elements).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | `random_state` pinned in all ML models; `requirements.txt` pins exact versions; Dataset fetched from canonical HuggingFace URL with checksum verification. | ✅ Pass |
| **II. Verified Accuracy** | All dataset citations in `research.md` restricted to the "Verified datasets" block. No invented URLs. | ✅ Pass |
| **III. Data Hygiene** | Raw data saved as `data/raw/` with checksum; processed data saved as `data/processed/` with derivation logs. No in-place modification. | ✅ Pass |
| **IV. Single Source of Truth** | **Traceability Matrix**: Every result in `paper/` or `output/` logs its source row ID in `data/processed/` and the specific code function in `code/`. `source_row_id` is preserved in all intermediate files. | ✅ Pass |
| **V. Versioning Discipline** | **State Directory**: `state/` directory created to store `artifact_hashes.yaml`. Every artifact generation step computes SHA-256 and updates this file. | ✅ Pass |
| **VI. Physical Descriptor Consistency** | `pymatgen` version pinned in `requirements.txt`. Descriptor calculation logic logged with version hash. | ✅ Pass |
| **VII. Prediction Uncertainty Quantification** | Bootstrapped ensemble and Domain of Applicability (Mahalanobis distance on PCA-reduced features) implemented to provide confidence intervals and risk flags. | ✅ Pass |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-effect-of-alloying-eleme/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/
├── code/
│ ├── __init__.py
│ ├── requirements.txt
│ ├── data/
│ │ ├── download.py # Fetches and verifies HuggingFace dataset
│ │ ├── ingest.py # Parses CSV, normalizes fractions
│ │ └── features.py # Pymatgen descriptor engineering
│ ├── models/
│ │ ├── train.py # RF/GB training, LOCO CV, model selection
│ │ ├── validate.py # Residual analysis (Breusch-Pagan), weighted retrain
│ │ └── predict.py # Screening, DoA, bootstrapping, ranking
│ ├── utils/
│ │ ├── novelty.py # Known alloys check (local file or fallback)
│ │ └── shap_utils.py # SHAP value generation
│ └── main.py # Orchestration script
├── data/
│ ├── raw/ # Downloaded CSVs (checksummed)
│ └── processed/ # Feature-engineered CSVs
├── state/ # Artifact hashes and versioning (Constitution Principle V)
│ └── artifact_hashes.yaml
├── output/
│ ├── best_model.pkl
│ ├── best_model_weighted.pkl
│ ├── shap_feature_importance.json
│ ├── candidates.csv
│ └── verification_requests.json
├── tests/
│ ├── contract/ # Validates against schema contracts
│ ├── integration/ # End-to-end pipeline tests
│ └── unit/ # Feature calculation unit tests
└── docs/ # Paper drafts, reports
```

**Structure Decision**: Single-project Python structure (`code/`) is selected to minimize overhead and ensure all scripts run in a single virtualenv. This aligns with the CPU-only, free-tier runner constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LOCO Cross-Validation** | Standard K-Fold may leak chemical family information (similar alloys in train/test). LOCO ensures generalizability to new chemical families. **Rule**: Assign to cluster of element with highest atomic fraction; tie-break by higher atomic number. | K-Fold would overestimate performance on chemically similar alloys. |
| **Bootstrapped Ensemble** | Single model prediction lacks uncertainty quantification required by Constitution Principle VII. | Single model prediction cannot provide confidence intervals for novel candidates. |
| **Domain of Applicability (DoA)** | Novel compositions may be far outside training distribution; naive extrapolation is risky. **Mitigation**: PCA reduction before DoA to handle high dimensions. | Ignoring DoA leads to high-confidence predictions on physically impossible compositions. |
| **Heteroscedasticity Handling** | Residual analysis (FR-010) ensures model validity; weighted loss corrects for non-constant variance. **Fallback**: If binning is unstable, use global variance model or Huber loss. | Ignoring heteroscedasticity biases error estimates and model selection. |

## Implementation Steps

### Phase 1: Data Ingestion & Feature Engineering
1. **Download**: Fetch `data.csv` from `. Verify SHA-256 checksum.
2. **Schema Verification**: Verify the dataset contains `composition` and `log10_Rc` (or `Rc`) columns. **Fail explicitly** if missing or if the file is a metadata index without these columns.
3. **Ingest**: Parse CSV. Verify `composition` and `Rc` (or `log10_Rc`) columns. Fail if missing.
4. **Normalize**: Ensure elemental fractions sum to 1.0 ± 0.01.
5. **Feature Engineering**: Compute descriptors (atomic radius, electronegativity, VEC, pairwise mismatch) using `pymatgen`.
6. **Traceability**: Log source row ID for each processed row in `data/processed/features.csv`.

### Phase 2: Model Training & Validation
1. **LOCO Split**: Assign each composition to a cluster based on the element with the **highest atomic fraction**. If tied, choose the element with the **higher atomic number**. Split data by cluster.
2. **Train**: Train RandomForest and GradientBoosting models with hyperparameter grid ≤ 30.
3. **Select**: Choose model with lowest LOCO-MAE.
4. **Residual Analysis**: Perform Breusch-Pagan test.
 - **If Heteroscedasticity Detected (p < 0.05)**:
 - **Attempt**: Bin residuals by feature-space quantiles (A minimum of sufficient samples per bin).
 - **Fallback**: If bins are too small/unstable, fit a global log-variance model or use Huber loss.
 - Retrain with weighted loss or robust loss. Save as `best_model_weighted.pkl`.
5. **SHAP**: Generate SHAP values for the best model.

### Phase 3: Screening & Ranking
1. **Generate**: Create all unique ternary combinations from the most abundant elements.
2. **Predict**: Predict $log_{10}(R_c)$ using the best model.
3. **DoA Check**:
 - Reduce feature space to PCA components (retaining [deferred] variance).
 - Calculate Mahalanobis distance.
 - **Penalty**: If outside DoA, add **+1.0** to $log_{10}(R_c)$ (Spec FR-009).
 - *Scientific Note*: While a continuous penalty might be scientifically superior, the fixed +1.0 penalty is a strict requirement of FR-009. The `risk_score` (Mahalanobis distance) is also output to allow downstream re-analysis.
4. **Filter**: Retain candidates with $log_{10}(R_c) < 4.0$ (absolute physical cutoff) AND in the lower tail of the dataset distribution.
5. **Novelty Check**: Query `data/known_alloys.csv` if present. If not, set `novelty_status` to `unverified_external`.
6. **Rank**: Sort by ascending `final_score` (predicted + penalty). Output a ranked subset of top results.
7. **Output**: Generate `candidates.csv` (schema: `contracts/candidates_csv.schema.yaml`) and `verification_requests.json` (schema: `contracts/verification.schema.yaml`).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset missing `log10_Rc` | Pipeline failure | Explicit check in `download.py`; fail fast with clear error. |
| Pymatgen missing element | Data loss | Log warning, exclude row, continue. |
| No candidates below threshold | Empty output | Output empty CSV with header; log message. |
| Novelty list unavailable | False "novel" claims | Flag as "unverified_external" in `verification_requests.json`. |
| Heteroscedasticity | Biased model | Implement weighted retraining with binning safeguards or global fallback (FR-010). |
| Spec vs. Science Conflict (DoA) | Model bias | Implement +1.0 penalty as per FR-009; document as known limitation; output `risk_score`. |
| Dimensionality in DoA | False flags | Use PCA reduction before Mahalanobis calculation. |
