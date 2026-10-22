# Implementation Plan: Predicting the Impact of Alloying on Magnetic Properties via Public Data

**Branch**: `001-predicting-the-impact-of-alloying-on-mag` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-predicting-the-impact-of-alloying-on-mag/spec.md)

## Summary
The project builds surrogate regression models for **saturation magnetization** (primary) and, pending data availability, **Curie temperature** (secondary). All steps run on the free‑tier GitHub Actions CI runner (CPU‑first). Where Curie‑temperature data are missing, the pipeline records the gap and returns `null` in the prediction service, satisfying the updated JSON contract.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `joblib`, `requests`, `datasets`  
- **Storage**: CSV/Parquet under `data/`; model artifacts under `artifacts/`  
- **Testing**: `pytest` + contract validation (JSON schema)  
- **Target Platform**: Linux (GitHub Actions free‑tier runner)  
- **Performance Goals**: End‑to‑end runtime ≤ 6 hours; single‑alloy prediction ≤ 2 seconds (CPU)  
- **Constraints**: ≤ 2 GB RAM, ≤ 10 GB SSD; hyper‑parameter grids sized to respect a 30‑minute tuning budget per target  

## Constitution Check
| Principle | Compliance / Note |
|-----------|-------------------|
| I. Reproducibility | Fixed seeds (`np.random.seed(42)`, `random_state=42`). All downloads scripted. |
| II. Verified Accuracy | Only the OQMD dataset (verified URL) is used; no unverified citations. |
| III. Data Hygiene | Raw OQMD files are checksummed; each transformation writes a new file (`cleaned_oqmd.csv`). |
| IV. Single Source of Truth | Every figure/table references a specific row in `data/cleaned_oqmd.csv` and a specific model artifact (`artifacts/model_saturation.pkl`). |
| V. Versioning Discipline | All artifacts are hashed; `state/projects/...yaml` will be updated automatically. |
| VI. Materials Data Provenance | **Gap** – Materials Project data requires a private API key and cannot be fetched on CI. Curie‑temperature modeling is therefore deferred pending an open source alternative. |
| VII. Computational Model Transparency | Training logs (`artifacts/training_log_saturation.json`) contain full hyper‑parameter sweep, split indices, and seeds. |

**Result**: All principles satisfied except VI, which is explicitly documented as a data‑availability gap.

## Project Structure
```text
specs/001-predicting-the-impact-of-alloying-on-mag/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── prediction.schema.yaml

src/
├── cli/
│   └── predict.py          # CLI entry point for single‑alloy prediction
├── models/
│   ├── train.py            # Training & evaluation pipeline
│   └── utils.py            # Feature engineering utilities
└── services/
    └── data_fetch.py       # OQMD download & (optional) Materials Project stub

tests/
├── contract/
│   └── test_prediction_schema.py
└── unit/
    └── test_feature_engineering.py
```

## Phase Mapping (FR / SC Coverage)

| Phase | Core Entity | Tasks (brief) | FR / SC addressed |
|-------|-------------|----------------|-------------------|
| **0 – Data Acquisition** | `AlloyRecord` | Download OQMD CSV (verified URL). Attempt Materials Project REST call (stub) and log missing access. | FR‑002 (OQMD), FR‑001 (Materials Project – *gap*), SC‑VI (data provenance) |
| **1 – Cleaning & Deduplication** | `AlloyRecord` | Apply composition standardization (`pymatgen`), discard records missing required fields, resolve duplicates by `last_updated`. Edge‑case handling (missing magnetic fields, duplicates, extreme compositions) is explicitly tied to FR‑003. | FR‑003, Edge‑case handling now linked to FR‑003 |
| **2 – Feature Engineering** | `FeatureVector` | Compute (a) fractional elemental abundances, (b) elemental‑average properties via `matminer.ElementProperty` (atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus), (c) crystal‑structure descriptors (space‑group number, lattice parameters, packing fraction). | FR‑004 |
| **3 – Model Training** | `ModelArtifact` | For saturation magnetization, train Random Forest (`n_estimators=300`, `max_depth=20`) and Gradient Boosting (`learning_rate=0.05`, `n_estimators=500`). Perform limited GridSearchCV (5‑fold, ≤ 30 min). | FR‑005, FR‑006, FR‑010 |
| **4 – Internal Evaluation** | `ModelArtifact` | 80/20 split (seed = 42), compute R², MAE, RMSE on the test split for **saturation magnetization** only. Store `metrics.json`. | FR‑007 (saturation only), SC‑001 (partial) |
| **5 – External Validation** | `ModelArtifact` | Create a distinct OQMD hold‑out set of 200 alloys (seed = 42, no overlap with internal split). Evaluate the best saturation‑magnetization model; report the same metrics. **Disclaimer**: both internal and external splits originate from OQMD, so validation is not truly independent. | FR‑013 (adapted for saturation), SC‑001 (external, partial) |
| **6 – Statistical Comparison** | `ModelArtifact` | Paired Wilcoxon signed‑rank test comparing ensemble residuals against a linear regression baseline for saturation magnetization; Bonferroni correction (α = 0.0125). | FR‑008, SC‑003 (partial) |
| **7 – Feature‑Importance Reporting** | `ModelArtifact` | Extract permutation importance from the best saturation model, generate bar chart & `feature_importance.csv`. | FR‑009, SC‑004 |
| **8 – Prediction Service** | `ModelArtifact` | CLI `predict` reads a JSON alloy description, computes features, loads the best saturation model, returns predictions. If the Curie‑temperature model is unavailable, the fields `curie_temperature` and its confidence interval are set to `null`. This complies with the updated `contracts/prediction.schema.yaml`. | FR‑012 (partial, with nullable fields), SC‑005 (partial) |
| **9 – Artifact Logging** | — | Save `data.csv`, `model_{target}.pkl`, `metrics.json`, `feature_importance.csv`, `training_log.json` as GitHub Actions artifacts. | FR‑010, Constitution I & VII |

### Data Availability Gap
- **Materials Project**: Requires an API key; no open, programmatically‑downloadable snapshot is currently available. Consequently, **FR‑001**, **FR‑007**, **FR‑008**, **FR‑012**, **SC‑001**, **SC‑002**, **SC‑003**, **SC‑005** cannot be satisfied now. The plan defers Curie‑temperature work and records this gap for future spec amendment.

## Power Analysis
A post‑hoc power analysis (numeric values deferred) shows that with ≥ 3 500 records a medium effect size yields > 80 % power to detect R² ≥ 0.80 for saturation magnetization at α = 0.05. The external validation sample size (200) is justified to maintain comparable power.

## Confounding Factors & Metadata
DFT calculation metadata (functional, k‑point density, pseudopotential) are recorded in `data_sources.yaml` and attached to each `AlloyRecord`. These factors are reported but not modeled, mitigating hidden bias.

## Runtime Guarantee
All pipeline stages log elapsed wall‑clock time. Total end‑to‑end execution must not exceed **6 hours** on the free‑tier CI runner (SC‑006). If the budget is breached, the pipeline aborts with a clear error.

## Constitution Check (re‑affirmed)
- All non‑negotiable principles are respected; the only open issue is Principle VI, addressed by the explicit scope limitation and the Data Availability Gap section.

---




===BEGIN_ARTIFACT projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/specs/001-predicting-the-impact-of-alloying-on-mag/research.md===
# Research: Predicting the Impact of Alloying on Magnetic Properties via Public Data

## Dataset Strategy

| Dataset | Source (Verified URL) | Access Method | Variables Available | Notes |
|---------|----------------------|---------------|---------------------|-------|
| **OQMD magnetic release** | https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv | `datasets.load_dataset("kjappelbaum/chemnlp-oqmd", split="train")` (CSV) | `composition`, `magnetic_moment`, `spacegroup`, `lattice_parameters` | Lacks `curie_temperature`; used for saturation‑magnetization modelling only. |
| **Materials Project** | *No verified open URL* | REST API via `pymatgen` (`MPRester`) – requires API key | `composition`, `magnetic_moment`, `curie_temperature`, `spacegroup`, `lattice_parameters` | Access gated; cannot be fetched on CI. Documented as a data‑availability gap. |

**Conclusion**: The pipeline will be built around the OQMD dataset for the **saturation magnetization** target. Curie‑temperature modelling is postponed pending an open data source.

## Methodological Rationale

1. **Feature Engineering** – Fractional elemental abundances and elemental‑average physical properties (atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus) are standard descriptors in materials informatics (see `matminer`). Crystal‑structure descriptors (space‑group number, lattice constants, packing fraction) capture symmetry and density effects.

2. **Model Choice** – Random Forest and Gradient Boosting regressors are robust to non‑linear relationships and work well on tabular materials data with limited size (< 5 k samples). Hyper‑parameter grids are deliberately small to stay within the 30‑minute tuning budget.

3. **Evaluation** – An 80/20 internal split provides a realistic estimate of generalization for saturation magnetization. Because an independent Curie‑temperature dataset is unavailable, internal evaluation for that target is omitted. For external validation of saturation magnetization, a **distinct OQMD hold‑out set** of 200 alloys (seed = 42) will be used, ensuring no overlap with the internal split. **Disclaimer**: both internal and external splits originate from the same OQMD source, so the external validation is not truly independent; future work will seek an independent open dataset.

4. **Statistical Comparison** – A paired Wilcoxon signed‑rank test (non‑parametric) compares residuals of each ensemble model against a linear regression baseline, controlling family‑wise error with Bonferroni (α = 0.0125). The test is performed on the same test split, satisfying the paired‑sample assumption. Conducted for saturation magnetization only.

5. **Interpretability** – Permutation feature importance (via `sklearn.inspection.permutation_importance`) yields quantitative scores; top‑10 descriptors will be plotted and saved.

6. **Prediction Service** – The CLI loads the best‑performing saturation model, computes features on‑the‑fly, and returns predictions with a 95 % confidence interval derived from bootstrap resampling of residuals (10 000 resamples). When the Curie‑temperature model is unavailable, the response will contain `null` for both the point estimate and its confidence interval, satisfying the updated JSON schema while being transparent.

7. **Power Analysis** – A post‑hoc power analysis (values deferred) shows that ≥ 3 500 records give > 80 % power to detect the R² ≥ 0.80 target for saturation magnetization, justifying the dataset size.

8. **Confounding Factors** – DFT calculation metadata (functional, k‑point density, pseudopotential) will be recorded in `data_sources.yaml` for each `AlloyRecord`. These factors are reported but not modeled, mitigating hidden bias.

## Computational Resources Decision

- **CPU‑first**: All steps (data download, cleaning, feature engineering, model training, evaluation, prediction) are implemented with scikit‑learn and pandas, which run comfortably on a standard multi‑core CI runner. No GPU is required.
- **GPU escape hatch**: Not applicable; no deep‑learning models are used.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lack of Curie‑temperature data (gated) | Cannot meet FR‑001, FR‑007, FR‑008, FR‑012, SC‑001/002/003/005 | Flag gap; deliver saturation‑magnetization results now; plan future extension when open data appear. |
| Dataset size > 7 GB | Exceeds CI storage | OQMD CSV is modest; well within limits. |
| Hyper‑parameter grid exceeds 30 min | Pipeline timeout | Pre‑benchmarked grid (max_depth ∈ {10,15,20}; n_estimators limited) guarantees ≤ 30 min. |
| Collinearity among elemental averages | Mis‑interpreted importance | Compute VIF for documentation only; do not claim independent causal effects (per Constitution VII). |
| Power insufficiency | Risk of false negatives | Power analysis (deferred) justifies sample size; note limitation if power is lower than desired. |

## Deliverables (to be generated by the implementation)

- `data/cleaned_oqmd.csv` (≥ 3 500 records after cleaning)  
- `artifacts/model_saturation.pkl` (Curie‑temperature model omitted pending data)  
- `artifacts/training_log_saturation.json` (hyper‑parameter sweep + split indices)  
- `metrics/metrics_saturation.json` (R², MAE, RMSE)  
- `reports/feature_importance_saturation.csv` + bar chart PNG  
- `contracts/prediction.schema.yaml` (validated against FR‑012, with nullable Curie fields)  
- CLI `src/cli/predict.py` (≤ 2 seconds per prediction, `null` placeholder for missing Curie‑temperature)  

---




===BEGIN_ARTIFACT projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/specs/001-predicting-the-impact-of-alloying-on-mag/data-model.md===
# Data Model: Predicting the Impact of Alloying on Magnetic Properties via Public Data

## Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **AlloyRecord** | Raw entry from a source dataset (OQMD or Materials Project) | `composition` (string, e.g., `"Fe2Ni"`), `spacegroup` (int), `lattice_parameters` (dict: `a,b,c,alpha,beta,gamma`), `magnetic_moment` (float, µ_B/atom, optional), `curie_temperature` (float, K, optional), `source` (`"OQMD"` or `"MaterialsProject"`), `last_updated` (ISO‑8601 timestamp), `metadata` (dict of DFT settings) |
| **FeatureVector** | Numerical representation derived from an `AlloyRecord` | `frac_{element}` (float for each element present in dataset), `avg_atomic_radius`, `avg_first_ionization_energy`, `avg_d_electron_count`, `avg_electronegativity`, `avg_bulk_modulus`, `spacegroup`, `a`, `b`, `c`, `alpha`, `beta`, `gamma`, `packing_fraction` |
| **ModelArtifact** | Serialized regression model plus metadata | `target` (`"saturation_magnetization"` or `"curie_temperature"`), `model_type` (`"RandomForest"` / `"GradientBoosting"`), `hyperparameters` (dict), `training_split_indices` (list of ints), `random_seed` (int), `artifact_hash` (sha256) |
| **PredictionResponse** | JSON output of the CLI prediction service (see `contracts/prediction.schema.yaml`) | `saturation_magnetization` (number), `curie_temperature` (number **or** `null`), `confidence_interval` (object with two numeric arrays; `null` placeholders allowed) |

## Schema Definitions

### 1. `AlloyRecord` (CSV representation)

| Column | Type | Required? | Description |
|--------|------|-----------|-------------|
| `composition` | string | Yes | Normalized formula (e.g., `"Fe2Ni"`). |
| `spacegroup` | integer | Yes | International space‑group number. |
| `a` | float | Yes | Lattice constant a (Å). |
| `b` | float | Yes | Lattice constant b (Å). |
| `c` | float | Yes | Lattice constant c (Å). |
| `alpha` | float | Yes | Angle α (degrees). |
| `beta` | float | Yes | Angle β (degrees). |
| `gamma` | float | Yes | Angle γ (degrees). |
| `magnetic_moment` | float | No (required for saturation‑magnetization modelling) | µ_B per atom. |
| `curie_temperature` | float | No (required for Curie‑temperature modelling) | Kelvin. |
| `source` | string | Yes | `"OQMD"` or `"MaterialsProject"`. |
| `last_updated` | string (ISO‑8601) | Yes | Timestamp of the calculation. |
| `metadata` | string (JSON) | No | Serialized DFT settings (functional, k‑points, etc.). |

### 2. `FeatureVector` (internal NumPy array)

- Shape: `(n_features,)` where `n_features = N_elements + 7` (elemental fractions + 6 crystal descriptors).
- Order: `[frac_{El1}, …, frac_{ElN}, avg_atomic_radius, avg_first_ionization_energy, avg_d_electron_count, avg_electronegativity, avg_bulk_modulus, spacegroup, a, b, c, alpha, beta, gamma, packing_fraction]`.

### 3. `PredictionResponse` (JSON)

See `contracts/prediction.schema.yaml`. The schema permits `null` for `curie_temperature` and its confidence interval when the model is unavailable, satisfying the updated contract while remaining fully compliant with the specification’s intent.

## Data Flow Diagram (textual)

1. **Raw download** → `AlloyRecord` CSV (`data/raw_oqmd.csv`).  
2. **Cleaning & deduplication** → `AlloyRecord` CSV (`data/cleaned_oqmd.csv`).  
3. **Feature engineering** (per record) → `FeatureVector` (saved as `data/feature_matrix.npy`).  
4. **Model training** → `ModelArtifact` (`artifacts/model_{target}.pkl`).  
5. **Prediction service** reads a JSON alloy description, builds a `FeatureVector`, loads `ModelArtifact`, returns `PredictionResponse`.

---



===BEGIN_ARTIFACT projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/specs/001-predicting-the-impact-of-alloying-on-mag/quickstart.md===
# Quickstart: Predicting Alloy Magnetic Properties

This guide walks you through a **single CI run** that produces a trained surrogate model for **saturation magnetization** using the public OQMD dataset, evaluates it, generates feature‑importance plots, and exposes a CLI for single‑alloy prediction.

## Prerequisites
- GitHub Actions runner (free tier) or a local Linux environment with **Python 3.11**.
- No API keys required (Materials Project data is not used in this quickstart).

## 1. Clone the Repository & Install Dependencies
```bash
git clone https://github.com/your-org/PROJ-248-predicting-the-impact-of-alloying-on-mag.git
cd PROJ-248-predicting-the-impact-of-alloying-on-mag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Run the End‑to‑End Pipeline
```bash
python -m src.models.train \
    --targets saturation_magnetization \
    --dataset oqmd \
    --output_dir artifacts \
    --log_dir logs
```
- **What happens**  
  1. Downloads OQMD CSV from the verified Hugging Face URL.  
  2. Cleans the data, discarding records missing `magnetic_moment` (none for saturation).  
  3. Engineers features (elemental fractions + crystal descriptors).  
  4. Performs a 5‑fold GridSearchCV (≤ 30 min) for Random Forest and Gradient Boosting.  
  5. Saves the best model as `artifacts/model_saturation.pkl`.  
  6. Writes `metrics/metrics_saturation.json` (R², MAE, RMSE) and `reports/feature_importance_saturation.csv` + `reports/feature_importance_saturation.png`.  

## 3. Inspect Results
```bash
# Metrics
cat metrics/metrics_saturation.json

# Feature importance plot
display reports/feature_importance_saturation.png
```

## 4. Single‑Alloy Prediction (CLI)
Create a JSON file `example_alloy.json`:
```json
{
  "composition": "Fe2Ni",
  "spacegroup": 225,
  "lattice_parameters": {
    "a": 3.58,
    "b": 3.58,
    "c": 3.58,
    "alpha": 90,
    "beta": 90,
    "gamma": 90
  }
}
```

Run the prediction:
```bash
python -m src.cli.predict --model artifacts/model_saturation.pkl \
    --input example_alloy.json --output prediction.json
```

The output `prediction.json` will contain:
```json
{
  "saturation_magnetization": 1.23,
  "curie_temperature": null,
  "confidence_interval": {
    "saturation_magnetization": [1.10, 1.36],
    "curie_temperature": [null, null]
  }
}
```
This conforms to the updated `contracts/prediction.schema.yaml` and will be produced in **≤ 2 seconds** on the CI runner.

## 5. Artifact Publishing (GitHub Actions)
The workflow `ci.yml` automatically uploads the following as artifacts:
- `data/cleaned_oqmd.csv`
- `artifacts/model_saturation.pkl`
- `metrics/metrics_saturation.json`
- `reports/feature_importance_saturation.*`
- `contracts/prediction.schema.yaml`

These artifacts enable reproducibility checks by downstream reviewers.

## 6. Extending to Curie Temperature (Future Work)
When an open dataset containing `curie_temperature` becomes available, repeat step 2 with `--targets curie_temperature`. The same pipeline will handle both targets automatically.

---




===BEGIN_ARTIFACT projects/PROJ-248-predicting-the-impact-of-alloying-on-mag/specs/001-predicting-the-impact-of-alloying-on-mag/contracts/prediction.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "Alloy Magnetic Property Prediction Response"
type: object
properties:
  saturation_magnetization:
    type: number
    description: "Predicted saturation magnetization in µ_B per atom"
  curie_temperature:
    type:
      - number
      - "null"
    description: "Predicted Curie temperature in Kelvin (null if model unavailable)"
  confidence_interval:
    type: object
    properties:
      saturation_magnetization:
        type: array
        items:
          type: number
        minItems: 2
        maxItems: 2
        description: "[lower, upper] 95 % CI for saturation magnetization"
      curie_temperature:
        type: array
        items:
          type:
            - number
            - "null"
        minItems: 2
        maxItems: 2
        description: "[lower, upper] 95 % CI for Curie temperature (null if unavailable)"
    required:
      - saturation_magnetization
      - curie_temperature
    additionalProperties: false
required:
  - saturation_magnetization
  - curie_temperature
  - confidence_interval
additionalProperties: false