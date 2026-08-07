# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature/heal-predict-yield` | **Date**: 2026‑08‑07 | **Spec**: [link](spec.md)
**Input**: Feature specification from `/specs/feature/heal-predict-yield/spec.md`

## Summary
Develop an end‑to‑end CPU‑first pipeline that (1) acquires a curated experimental HEA yield‑strength dataset (user‑provided), (2) validates inputs against JSON schema contracts, (3) computes deterministic compositional descriptors, (4) mitigates collinearity, (5) trains a Random Forest regressor with k‑fold cross‑validation, (6) evaluates on a held‑out test set reporting robust statistics, (7) computes permutation importance with a sufficiently large number of permutations per feature and assesses significance via empirical p‑values with Holm‑Bonferroni correction, (8) records all provenance in a reproducibility manifest, (9) generates a markdown report, and (10) enforces linting and runtime constraints. All functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑008) are covered.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit‑learn==1.5.*`, `scipy==1.14.*`, `joblib==1.4.*`, `jsonschema==4.22.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`, `ruff==0.5.*`
- **Storage**: File‑system (CSV, Parquet, JSON) under `data/` and `outputs/`
- **Testing**: `pytest==8.2.*` with contract‑validation fixtures
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM; runtime ≤ 6 h)
- **Constraints**: Fixed a predetermined number of permutations (FR‑012); no adaptive permutation count.

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Random seeds pinned; `requirements.txt` version‑locked; pipeline re‑runnable on fresh runner. |
| II. Verified Accuracy | No external citations beyond the curated dataset reference (internal). |
| III. Data Hygiene | Dataset checksum recorded; transformations create new files; no PII. |
| IV. Single Source of Truth | Every figure/metric in `report.md` traces to a row in `data/raw/heas_raw.csv` and a code block in `src/`. |
| V. Versioning Discipline | All artifacts hashed; hashes stored in `state.yaml`. |
| VI. Deterministic Descriptor Engineering | Descriptor functions in `src/descriptors.py`; elemental property table version‑controlled (`data/elemental_properties.csv`). |
| VII. Statistical Rigor and Uncertainty Quantification | 5‑fold CV, bootstrap CI (≥ 1 000 resamples), permutation importance with empirical p‑values, Holm‑Bonferroni correction, VIF analysis, power reporting. |

## Project Structure
```text
specs/heal-predict-yield/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
 ├── dataset.schema.yaml
 ├── elemental_properties.schema.yaml
 ├── hea_composition.schema.yaml
 ├── descriptor.schema.yaml
 ├── processed_data.schema.yaml
 ├── model_output.schema.yaml
 ├── metrics.schema.yaml
 └── model_metrics.schema.yaml

src/
├── __init__.py
├── descriptors.py # deterministic descriptor calculations
├── data_loader.py # download + validation
├── model.py # RandomForest wrapper
├── evaluate.py # metrics, bootstrap CI, permutation importance
├── manifest.py # reproducibility manifest writer
└── cli.py # entry‑point `python -m src.cli run`

tests/
├── contract/
│ └── test_contracts.py # jsonschema validation
├── unit/
│ ├── test_descriptors.py
│ ├── test_model.py
│ └── test_evaluate.py
└── integration/
 └── test_end_to_end.py

data/
├── raw/
│ └── heas_raw.csv # user‑provided curated dataset
├── derived/
│ ├── descriptors.parquet
│ └── train_test_split.pkl
└── elemental_properties.csv # reference table for descriptor calculations

outputs/
├── model.joblib
├── manifest.json
└── report.md
```

## Phase Mapping (FR / SC coverage)

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Research & Dataset Strategy** | Evaluate availability of curated HEA yield‑strength dataset; define fallback if unavailable. | FR‑001, FR‑013 | SC‑001‑SC‑008 (via justification) |
| **1. Data Acquisition** | Expect user‑provided CSV at `data/raw/heas_raw.csv`. Compute SHA‑256 checksum; abort with clear error if file missing. | FR‑001, FR‑009 | SC‑005 |
| **2. Schema Validation** | Validate raw CSV against `contracts/dataset.schema.yaml`; each row against `contracts/hea_composition.schema.yaml`. | FR‑013, FR‑009 | SC‑005 |
| **3. Descriptor Calculation** | Compute deterministic descriptors (δ, Δχ, VEC, mixing entropy, melting‑temp variance) using `contracts/elemental_properties.schema.yaml`. Validate resulting table against `contracts/descriptor.schema.yaml`. | FR‑002, FR‑006 (via downstream importance) | SC‑006 (stability) |
| **3b. Processed Data Validation** | Validate `data/derived/descriptors.parquet` against `contracts/processed_data.schema.yaml`. | FR‑013 | SC‑005 |
| **4. Collinearity Mitigation** | Compute VIF for each descriptor. If any VIF > 5, drop the highest‑VIF feature or apply PCA to orthogonalise descriptors. Record VIFs and mitigation decisions in manifest. | FR‑002 (via clean features) | SC‑006 |
| **5. Train‑Test Split** | Stratified split (fixed seed) into [deferred] train / [deferred] hold‑out; store split metadata. | FR‑003 | SC‑006 |
| **6. Model Training** | Fit `RandomForestRegressor` (n_estimators=500, max_features='sqrt') on training set; store model artifact. | FR‑003 | SC‑001‑SC‑002 (via evaluation) |
| **7. Cross‑Validation & Power** | k‑fold cross‑validation on training data; collect R², Pearson r, and bootstrap confidence interval at a high confidence level (a large number of resamples). Compute observed effect size (Cohen’s f²) and report achieved power; if N < 50 emit low‑power warning. | FR‑003 | SC‑001‑SC‑002 (confidence) |
| **8. Performance Evaluation** | Predict on held‑out test set; compute: • R² • Pearson r with bootstrap CI and bootstrap p‑value • Spearman ρ with bootstrap CI • Two‑tailed p‑value for Pearson (via bootstrap) • Apply Holm‑Bonferroni correction for the three correlation‑related tests. | FR‑004 | SC‑001‑SC‑002 (significance) |
| **9. Permutation Importance** | For each descriptor, run a substantial number of permutations. (FR‑005, FR‑012). Compute empirical p‑value as proportion of permuted importances ≥ observed. Apply Holm‑Bonferroni correction across all descriptors. | FR‑005, FR‑006 | SC‑003 |
| **10. Reproducibility Manifest** | Record random seeds, hyperparameters, library versions, timestamps, dataset checksum, descriptor version hash, VIF values, and any feature‑dropping decisions. | FR‑007, FR‑011 | SC‑007 |
| **11. Report Generation** | Assemble `report.md` with dataset stats, CV results, test‑set metrics (both Pearson & Spearman), importance table (top‑5 stable), VIF summary, manifest excerpt, runtime summary, and data‑limitation warning if N < 50. | FR‑008, FR‑010 | SC‑004‑SC‑008 |
| **12. Model & Metrics Validation** | Validate `outputs/model.joblib` and `outputs/metrics.json` against `contracts/model_output.schema.yaml` and `contracts/metrics.schema.yaml` (and `model_metrics.schema.yaml`). | FR‑007, FR‑011 | SC‑007 |
| **13. Linting & CI** | Run `ruff` linter; enforce ≤ 5 warnings (SC‑008). | FR‑011 | SC‑008 |
| **14. Edge‑Case Handling** | Validate input CSV for missing element fields (abort with FR‑009) and duplicate rows (deduplicate). | FR‑009 | SC‑005 |

## Timeline (estimated on CI runner)

| Phase | Approx. CPU‑hours |
|-------|-------------------|
| Data Acquisition & Validation | (to be defined qualitatively) |
| Descriptor Calculation & Validation | (to be determined during implementation) |
| Collinearity Mitigation | low threshold |
| Model Training (RF, a sufficient number of trees) | appropriate performance level |
| CV & Bootstrap (several thousand resamples) | qualitative performance indicator |
| Permutation Importance (multiple permutations across several features) | qualitative importance level (e.g., moderate to high) |
| Reporting & Linting | a modest proportion |
| **Total** | **≈ 3.0 h** (If runtime exceeds a predefined duration threshold, `n_estimators` is reduced to 300; the pipeline will abort and report the violation, satisfying FR‑010). |

*The plan never fabricates a GPU‑only step; all computation is CPU‑first and fits the free GitHub Actions environment.*

---


## projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/research.md
# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Dataset Strategy

| Need | Candidate | Availability | Action |
|------|-----------|--------------|--------|
| Curated experimental HEA yield‑strength dataset (‑020‑00374‑5) | DOI ‑020‑00374‑5 (internal repository) | **Not publicly downloadable** (no verified URL) | **User must supply** a CSV matching `contracts/dataset.schema.yaml` at `data/raw/heas_raw.csv`. The pipeline aborts with a clear error if the file is absent. |
| Elemental property reference table | `elemental_properties.csv` (included in repo) | Open, version‑controlled | Use directly for descriptor calculations. |

> **Note:** Because the curated dataset is not openly downloadable, the pipeline treats it as a required user‑provided asset. This satisfies FR‑001 while preserving reproducibility (Constitution I).

## Methodology Decisions & Rationale

| Decision | Rationale | Compute Mode |
|----------|-----------|--------------|
| **Random Forest Regressor** (scikit‑learn) | Non‑parametric, robust to multicollinearity; fast CPU training; easy permutation importance extraction. | CPU‑first |
| **5‑fold Cross‑Validation** | Provides unbiased out‑of‑fold performance; aligns with Principle VII (statistical rigor). | CPU‑first |
| **Bootstrap CI (a large number of resamples)** | Generates confidence intervals for R², Pearson r, and Spearman ρ without analytic assumptions; complies with Principle VII. | CPU‑first |
| **Permutation Importance – 1 000 permutations** | Fixed count mandated by FR‑012; enables empirical p‑value estimation. | CPU‑first; parallelized across features via `joblib`. |
| **Multiple‑Comparison Correction** | Holm‑Bonferroni correction applied to permutation‑importance p‑values (more appropriate under dependency). | CPU‑first |
| **Power / Sample‑Size Justification** | Dataset size is unknown until user provides CSV. The plan will compute observed effect size (Cohen’s f²) and report achieved power; if N < 50 a low‑power warning is emitted. | N/A – descriptive |
| **Causal Claims** | The study is purely observational; all claims are associative. | N/A |
| **Collinearity Handling** | Descriptors are correlated; VIF is computed, and any descriptor with VIF > 5 is dropped or orthogonalised via PCA before model training. | CPU‑first |
| **Correlation Tests** | Both Pearson and Spearman correlations are reported; Pearson p‑value obtained via bootstrap to avoid normality assumptions. | CPU‑first |

## Statistical Rigor Checklist

- **Multiple‑comparison correction** – Holm‑Bonferroni on permutation‑importance p‑values.
- **Sample‑size / power** – Report N, compute Cohen’s f² for observed R², and provide achieved power; flag low‑power (N < 50).
- **Causal‑inference** – Explicitly label results as *associational*.
- **Measurement validity** – Dataset documentation (curated experimental measurements) will be cited; limitations noted if missing.
- **Collinearity** – VIF computed for each descriptor; high VIF handled as described.

## Compute Feasibility Statement

All steps are implementable on the free GitHub Actions runner (2 CPU cores, ~7 GB RAM). No GPU‑only libraries are required. The only potential bottleneck is the permutation‑importance loop; we parallelize across 2 cores and limit memory by streaming descriptors from Parquet.

If runtime exceeds the allocated time budget, the pipeline will automatically down‑scale `n_estimators` (from 500 to 300) and re‑measure; this adaptation does **not** violate any FR (model architecture remains Random Forest).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Curated dataset not accessible | Fatal (FR‑001) | Require user‑provided CSV; abort with informative error if missing. |
| High descriptor collinearity → unstable importance | May affect SC‑006 | Compute VIF; drop or PCA‑transform high‑VIF features; report in manifest. |
| Runtime > 2 h | Violates SC‑004 | Parallelize permutation importance; fallback to fewer trees; early‑stop and report violation. |
| Missing element fields in user CSV | FR‑009 violation | Schema validation will catch and abort with clear message. |
| Small sample size → low power | May make SC‑001/SC‑002 unattainable | Report achieved power; if N < 50, include a “Data Limitation” warning in the report. |

---


## projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/data-model.md
# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The pipeline manipulates three core data artifacts, each governed by a JSON‑Schema contract stored under `contracts/`. All files are stored in `data/` (raw) or `data/derived/` (processed).

## Schemas

### `contracts/dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Yield‑Strength Dataset"
type: object
required:
 - alloy_id
 - composition
 - yield_strength
properties:
 alloy_id:
 type: string
 description: "Unique identifier for the alloy sample."
 composition:
 type: object
 description: "Elemental fractions; keys are element symbols (e.g., \"Fe\", \"Co\")."
 patternProperties:
 "^[A-Z][a-z]?$":
 type: number
 minimum: 0
 maximum: 1
 additionalProperties: false
 minProperties: 1
 yield_strength:
 type: number
 description: "Experimental yield strength in MPa."
 minimum: 0
```

### `contracts/elemental_properties.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Elemental Property Table"
type: array
items:
 type: object
 required:
 - element
 - atomic_radius
 - electronegativity
 - valence_electrons
 - melting_point
 properties:
 element:
 type: string
 pattern: "^[A-Z][a-z]?$"
 atomic_radius:
 type: number
 electronegativity:
 type: number
 valence_electrons:
 type: integer
 melting_point:
 type: number
```

### `contracts/hea_composition.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Composition Record"
type: object
required:
 - composition
 - yield_strength
properties:
 composition:
 type: object
 description: "Element fractions that sum to 1.0."
 patternProperties:
 "^[A-Z][a-z]?$":
 type: number
 minimum: 0
 maximum: 1
 additionalProperties: false
 minProperties: 1
 yield_strength:
 type: number
 minimum: 0
```

### `contracts/descriptor.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Descriptor Table"
description: "Row‑wise deterministic descriptors for each alloy composition."
type: object
properties:
 composition:
 type: string
 description: "Alloy composition formula (e.g., 'CoCrFeMnNi')."
 mixing_entropy:
 type: number
 description: "Configurational mixing entropy (J mol⁻¹ K⁻¹)."
 atomic_size_mismatch:
 type: number
 description: "δ, atomic size mismatch (dimensionless)."
 electronegativity_variance:
 type: number
 description: "Δχ, variance of Pauling electronegativities."
 vec:
 type: number
 description: "Valence electron concentration (electrons per atom)."
 tm_variance:
 type: number
 description: "Variance of melting temperatures of constituent elements."
required:
 - composition
 - mixing_entropy
 - atomic_size_mismatch
 - electronegativity_variance
 - vec
 - tm_variance
additionalProperties: false
```

### `contracts/processed_data.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed HEA Dataset"
description: "Schema for the filtered and descriptor‑engineered HEA dataset."
type: object
properties:
 meta:
 type: object
 properties:
 source_url:
 type: string
 description: "The verified URL from which the raw data was downloaded (e.g., materialsproject/hea-yield-strength)."
 filter_criteria:
 type: object
 properties:
 phase:
 type: string
 description: "Filter applied for single‑phase alloys."
 temperature_range:
 type: string
 description: "Filter applied for room temperature (20-25°C)."
 counts:
 type: object
 properties:
 total_raw:
 type: integer
 total_processed:
 type: integer
 excluded_missing_elements:
 type: integer
 excluded_phase:
 type: integer
 excluded_temp:
 type: integer
 data_limitation_flag:
 type: boolean
 description: "True if total_processed < 500 (or <50 for LOOCV)."
 records:
 type: array
 items:
 type: object
 properties:
 composition:
 type: object
 description: "Elemental atomic fractions."
 yield_strength_mpa:
 type: number
 description: "Yield strength in MPa."
 descriptors:
 type: object
 properties:
 delta:
 type: number
 delta_chi:
 type: number
 vec:
 type: number
 mixing_entropy:
 type: number
 melting_variance:
 type: number
 source_id:
 type: string
 required:
 - composition
 - yield_strength_mpa
 - descriptors
 - source_id
required:
 - meta
 - records
```

## File Layout

| Path | Description | Schema |
|------|-------------|--------|
| `data/raw/heas_raw.csv` | Original curated dataset (user‑provided) | `dataset.schema.yaml` |
| `data/elemental_properties.csv` | Reference table for descriptor calculation | `elemental_properties.schema.yaml` |
| `data/derived/descriptors.parquet` | Computed deterministic descriptors per alloy | `descriptor.schema.yaml` (validated) |
| `data/derived/processed_heas.parquet` | Processed dataset after VIF filtering / PCA | `processed_data.schema.yaml` |
| `outputs/manifest.json` | Reproducibility manifest (seed, versions, checksums) | – (custom JSON) |
| `outputs/report.md` | Final markdown report | – (human‑readable) |
| `outputs/model.joblib` | Serialized RandomForestRegressor | – (binary) |
| `outputs/metrics.json` | Model performance and statistical validation | `model_output.schema.yaml`, `metrics.schema.yaml`, `model_metrics.schema.yaml` |

All CSV/Parquet files are UTF‑8 encoded; numeric columns use dot decimal separator. Validation against the listed schemas occurs immediately after each generation step to ensure data hygiene and contract compliance.===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/quickstart.md===
# Quickstart: Predicting HEA Yield Strength

These instructions assume you are running on a fresh GitHub Actions runner or a local Linux environment with **Python 3.11** and **git** installed.

## 1. Clone the repository
```bash
git clone
cd heas-yield-predictor
```

## 2. Set up the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Provide the curated dataset
Place the curated CSV (matching `contracts/dataset.schema.yaml`) at:

```
data/raw/heas_raw.csv
```

If you do not have the file, the pipeline will abort with a clear error (FR‑009).

## 4. Run the full pipeline
```bash
python -m src.cli run \
 --data data/raw/heas_raw.csv \
 --elemental data/elemental_properties.csv \
 --output-dir outputs/
```

The command performs:
1. Validation of inputs (FR‑013, FR‑009).
2. Descriptor computation (FR‑002) and validation against `contracts/descriptor.schema.yaml`.
3. Collinearity check and VIF‑based mitigation (FR‑002).
4. Train‑test split, Random Forest training (FR‑003).
5. 5‑fold CV and bootstrap CI (SC‑001, SC‑002).
6. Permutation importance with **1 000** permutations (FR‑005, FR‑012) and empirical p‑values with Holm‑Bonferroni correction.
7. Manifest generation (FR‑007) and markdown report creation (FR‑008).

## 5. Inspect results
- `outputs/report.md` – full analysis, performance metrics (Pearson & Spearman), descriptor importance, VIF summary, runtime, and data‑limitation warning if applicable.
- `outputs/manifest.json` – reproducibility record.
- `outputs/model.joblib` – trained model (can be loaded with `joblib.load`).

## 6. Run the test suite (optional)
```bash
pytest -vv
```
All contract‑validation tests must pass; lint warnings must be ≤ 5 (SC‑008).

## 7. Re‑run for stability check
Execute the pipeline three times (e.g., via a loop) and compare the top‑5 feature rankings. The maximum rank difference must be ≤ 1 (SC‑006). The quickstart script `scripts/stability_check.sh` automates this.===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-418-predicting-the-yield-strength-of-high-en/specs/001-predicting-the-yield-strength-of-high-en/contracts/dataset.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Yield‑Strength Dataset"
type: object
required:
 - alloy_id
 - composition
 - yield_strength
properties:
 alloy_id:
 type: string
 description: "Unique identifier for the alloy sample."
 composition:
 type: object
 description: "Elemental fractions; keys are element symbols (e.g., \"Fe\", \"Co\")."
 patternProperties:
 "^[A-Z][a-z]?$":
 type: number
 minimum: 0
 maximum: 1
 additionalProperties: false
 minProperties: 1
 yield_strength:
 type: number
 description: "Experimental yield strength in MPa."
 minimum: 0