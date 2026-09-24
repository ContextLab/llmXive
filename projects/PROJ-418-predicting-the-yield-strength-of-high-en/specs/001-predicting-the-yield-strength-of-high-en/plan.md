# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature/predict-hea-yield-strength` | **Date**: 2026-09-24 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/feature/predict-hea-yield-strength/spec.md`

## Summary
Develop an end‑to‑end reproducible pipeline that (1) downloads a publicly available high‑entropy alloy (HEA) yield‑strength dataset, (2) computes a deterministic set of compositional descriptors, (3) performs power analysis, multicollinearity screening, model training (Random Forest) with limited hyper‑parameter tuning, and evaluation on both an internal held‑out test set and an external validation set, (4) conducts descriptor‑target correlation analysis (including partial and Spearman correlations), (5) computes permutation importance with Holm‑Bonferroni correction, (6) assesses stability across three random seeds, and (7) generates a fully provenance‑tracked markdown report meeting all functional requirements (FR‑001 – FR‑024) and success criteria (SC‑001 – SC‑011).

## Technical Context

- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `pingouin==0.5.*`, `datasets==2.19.*`, `jsonschema==4.22.*`, `pyyaml==6.0.*`, `tqdm==4.66.*`
- **Storage**: Files under `data/` (raw, derived) and `output/` (models, reports)
- **Testing**: `pytest==8.2.*` + `jsonschema` validation tests
- **Target Platform**: Linux GitHub Actions runner (A modest number of CPU cores., ~7 GB RAM, ~a few‑tens of GB disk) – **CPU‑first**. All heavy computation (Random Forest, permutation importance) runs on CPU; no GPU is required.
- **Performance Goals**: Complete the full pipeline ≤ 6 h on the free‑tier runner.
- **Constraints**: Random seeds are pinned; all external data fetched from canonical URLs; pipeline aborts with clear messages if required verified URLs are missing.

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All random seeds are hard‑coded; all external data fetched from the same canonical URLs; pipeline is fully scriptable. |
| II. Verified Accuracy | All dataset URLs are required to appear in the verified‑datasets block; if absent, the pipeline aborts (see Phase 1). |
| III. Data Hygiene | Raw files are checksummed; every transformation produces a new file with a documented checksum. |
| IV. Single Source of Truth | Every numeric value in `report.md` is generated programmatically and linked to a provenance ID recorded in `manifest.json`. |
| V. Versioning Discipline | `requirements.txt` pins exact package versions; all artifacts are hashed and recorded in `state/projects/...yaml`. |
| VI. Deterministic Descriptor Engineering | Descriptor calculations use a single version‑controlled `elemental_properties.json` table; output checksums are recorded. |
| VII. Statistical Rigor and Uncertainty Quantification | 5‑fold CV, bootstrap CI (≥ 1000 resamples), permutation importance with Holm‑Bonferroni, power analysis (analytical + simulation), VIF screening are all performed as specified. |

## Phase Overview & FR/SC Mapping

| Phase | Description | Core FRs addressed | Core SCs addressed |
|-------|-------------|--------------------|--------------------|
| **0. Project Setup** | Create virtualenv, install pinned dependencies, copy `requirements.txt`. | FR‑010 (provenance log), FR‑013 (schema validation) | — |
| **0‑b. User‑Composition Validation** | Validate user‑provided composition CSV against `hea_composition.schema.yaml`; abort with clear error if missing fields. | FR‑009 | SC‑005 |
| **1. Data Acquisition** | • Download primary HEA yield‑strength dataset from a **verified Zenodo URL** (`). <br>• Download external validation dataset from a separate verified Zenodo release (`). <br>• Verify checksums; validate raw files against `dataset.schema.yaml`. | FR‑001, FR‑017, FR‑018 | — |
| **2. Descriptor Engineering** | • Load elemental property table from a verified HF dataset (`https://huggingface.co/datasets/MaterialsProject/elemental_properties`). <br>• Validate this table against `elemental_properties.schema.yaml`. <br>• Compute deterministic descriptors: atomic size mismatch (δ), mixing entropy (ΔS_mix), electronegativity variance (Δχ), valence electron concentration (VEC), melting‑temperature variance. <br>• Validate the descriptor table against `contracts/descriptor.schema.yaml`. | FR‑002, FR‑006, FR‑016, FR‑021 | — |
| **3. Power Analysis** | • Analytical power calculation using `statsmodels.stats.power.FTestPower` with effect size derived from literature (Cohen’s f² in the medium‑effect‑size range → R² indicating a substantial proportion of variance.) and `num_predictors` = final descriptor count. <br>• Additionally, run a simulation‑based Monte‑Carlo power estimate (using a sufficiently large number of resamples) for the Random Forest pipeline. <br>• Compare required N to actual N; abort with clear message if achieved power < 0.80. | FR‑015, FR‑022, FR‑023, FR‑015‑D, FR‑015‑S | SC‑009 |
| **4. Train‑Test Split & VIF Screening** | • Fixed random seed (e.g., 42) → 80/20 split. <br>• Compute VIF on training descriptors; drop any with VIF > 5 or apply ridge regularization. | FR‑016, FR‑010 | SC‑010 |
| **5. Model Training** | • Perform a limited hyper‑parameter grid search (`max_features` ∈ {‘sqrt’, ‘log2’}, `min_samples_leaf` ∈ {1,2,4}) evaluated via 5‑fold CV on the training set. <br>• Select the best configuration and train a `RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=2)`. <br>• Store model artifact (`model.pkl`). | FR‑003, FR‑005‑H (hyper‑parameter tuning) | — |
| **6. Cross‑Validation & Bootstrap CI** | • 5‑fold CV on training data → mean R², r, and 95 % bootstrap confidence intervals (≥ 1000 resamples). | FR‑003 | — |
| **7. Descriptor‑Target Correlation (Training)** | **7a. Pearson Correlation** – Compute Pearson r and two‑tailed p for each descriptor on training data. <br>**7b. Partial Correlation** – If optional metadata (e.g., processing temperature, synthesis route) are present, compute partial correlations controlling for these covariates. <br>**7c. Spearman Correlation** – Compute Spearman ρ to capture monotonic non‑linear relationships. <br>Report descriptors satisfying any of the following: (|r| > 0.5 & p < 0.01) OR (|ρ| > 0.5 & p < 0.01). | FR‑014, FR‑014‑C (partial), FR‑014‑NL (Spearman) | SC‑007 |
| **8. Internal Test Evaluation** | • Predict on held‑out test set. <br>• Compute R², Pearson r, and two‑tailed p‑value. <br>• Verify thresholds: R² ≥ 0.6, |r| ≥ 0.5, p < 0.05. | FR‑004, FR‑005 | SC‑001, SC‑002, SC‑003 |
| **9. Permutation Importance** | • A sufficient number of permutations per feature on the test set. <br>• Compute p‑values via non‑parametric permutation test. <br>• Apply Holm‑Bonferroni correction (α = 0.05). <br>• Flag features with corrected p < 0.05. | FR‑005, FR‑006 | SC‑003 |
| **10. External Validation** | **10a. Harmonization** – Document measurement protocols; if systematic differences exist, apply linear adjustment (ANCOVA) using available covariates. <br>**10b. Evaluation** – Compute R², r, p on the adjusted external set; require same success thresholds. | FR‑017, FR‑024, FR‑017‑H | SC‑008 |
| **11. Stability Assessment** | • Run the appropriate phases (up to the final phase) three independent times with distinct random seeds. <br>• Record the top feature rankings per run in `output/stability_rankings.json`. <br>• Compute maximum rank difference across runs; require ≤ 1. | FR‑021 | SC‑006 |
| **12. Reporting & Provenance** | • Assemble `report.md` with all sections required by FR‑008. <br>• Include dataset stats, VIF table, power‑analysis results (analytical & simulated), correlation tables (Pearson, partial, Spearman), CV performance, test & external metrics, permutation importance (adjusted p‑values), stability summary, and provenance manifest. <br>• Every numeric value is linked to a provenance ID from `manifest.json`. | FR‑008, FR‑010, FR‑019, FR‑024 | SC‑004, SC‑011 |
| **13. CI/Lint/Tests** | • Run `pytest` + schema validation tests. <br>• Run `ruff` (≤ 5 warnings) and `black --check`. <br>• Record results in `output/pipeline_runtime.json`. | T117‑T126 (implicit) | — |

## Deliverables (File Paths)

| Path | Description |
|------|-------------|
| `code/run_pipeline.py` | CLI entry point that orchestrates all phases. |
| `data/raw/hea_yield_strength.csv` | Downloaded primary dataset (validated). |
| `data/raw/hea_external_validation.csv` | Downloaded external validation set (validated). |
| `data/derived/descriptors.parquet` | Deterministic descriptor table. |
| `output/model.pkl` | Trained Random Forest model. |
| `output/metrics.json` | JSON with R², r, p‑values for test & external sets. |
| `output/importance.json` | Permutation‑importance scores + corrected p‑values. |
| `output/stability_rankings.json` | Top‑5 feature rankings for three seeds. |
| `output/manifest.json` | Provenance log (seeds, versions, checksums). |
| `report.md` | Final markdown report (FR‑008). |
| `output/pipeline_runtime.json` | CI status, runtime, lint results. |
| `contracts/*.schema.yaml` | JSON‑schema contracts (see `contracts/` folder). |

---


## Constitution Check
| Principle | Covered |
|-----------|---------|
| I. Reproducibility | ✅ |
| II. Verified Accuracy | ✅ (verified‑datasets enforced) |
| III. Data Hygiene | ✅ |
| IV. Single Source of Truth | ✅ |
| V. Versioning Discipline | ✅ |
| VI. Deterministic Descriptor Engineering | ✅ |
| VII. Statistical Rigor and Uncertainty Quantification | ✅ |