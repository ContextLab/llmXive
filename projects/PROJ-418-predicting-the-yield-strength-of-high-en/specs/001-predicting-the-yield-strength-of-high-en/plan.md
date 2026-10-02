# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `001-predicting-the-yield-strength-of-high-en` | **Date**: 2026-10-01 | **Spec**: [spec.md](../specs/001-predicting-the-yield-strength-of-high-en/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-the-yield-strength-of-high-en/spec.md`

## Summary
Develop an end‑to‑end reproducible pipeline that (1) ingests a real, openly‑accessible high‑entropy alloy (HEA) dataset from the Materials Project API, (2) computes a fixed set of composition‑only descriptors, (3) validates data and performs power analysis, (4) trains a Random Forest regressor, (5) evaluates on a held‑out test set and an independent external validation set, (6) conducts descriptor‑target correlation analysis, (7) computes permutation importance with Holm‑Bonferroni correction, (8) assesses stability across three random seeds, and (9) produces a fully provenance‑tracked markdown report.

All steps run on the CPU‑first GitHub Actions free tier; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `jsonschema`, `pyyaml`, `tqdm`, `matplotlib`, `seaborn`, `hydra-core`, `click`, `requests` (for Materials Project API)
- **Storage**: Files under `data/` (raw, derived, checksums) and `output/` (models, reports, artifacts)
- **Testing**: `pytest`, `jsonschema` validation tests
- **Target Platform**: Linux GitHub Actions runner (CPU‑first); ≤ 7 GB RAM, ≤ 6 h runtime
- **Performance Goals**: Entire pipeline ≤ 6 h on free runner, ≤ 7 GB RAM
- **Constraints**: All random seeds pinned; external datasets fetched from the same canonical source on every run.

## Constitution Check
| Principle | Check |
|-----------|-------|
| **I. Reproducibility** | All scripts are deterministic (seeded), dependencies pinned, and dataset acquisition is scripted via the Materials Project API. |
| **II. Verified Accuracy** | No external citations beyond the Materials Project API (publicly verified). |
| **III. Data Hygiene** | Every file written is checksum‑recorded in `data/checksums.yaml`. No in‑place mutation. |
| **IV. Single Source of Truth** | Every number in `report.md` is produced by a code block that logs a provenance ID linking back to the originating row in `data/`. |
| **V. Versioning Discipline** | Every artifact carries a SHA‑256 content hash recorded in `manifest.json` (explicitly noted in Constitution Check). |
| **VI. Deterministic Descriptor Engineering** | Descriptor functions live in `src/descriptors.py`; they use a frozen reference table (`data/elemental_properties.csv`) and are version‑controlled. |
| **VII. Statistical Rigor and Uncertainty Quantification** | 5‑fold CV, bootstrap CI (≥ 1000 resamples), permutation importance with Holm‑Bonferroni, and VIF assessment are all implemented and logged. |

## Phase‑by‑Phase Plan (maps every FR/SC)

| Phase | Tasks | FR/SC addressed |
|-------|-------|-----------------|
| **0. Project Setup** | • Create virtualenv, install `requirements.txt` (pinned). <br>• Validate `requirements.txt` against `contracts/requirements.schema.yaml`. | **FR‑001**, **FR‑018** (dependency validation) |
| **1. Data Acquisition** | • Query the Materials Project REST API for single‑phase HEA entries with experimentally measured `yield_strength`. <br>• Store raw records as `data/hea_raw.jsonl`. <br>• Validate against `contracts/dataset.schema.yaml`. | **FR‑001**, **FR‑013** |
| **2. Descriptor Calculation** | • Load `data/elemental_properties.csv`. <br>• Compute descriptors defined in Principle VI (mixing entropy, δ, Δχ, VEC, Tm variance). <br>• Output `data/descriptors.parquet`. <br>• Validate against `contracts/descriptor.schema.yaml` **and** `contracts/hea_schema.schema.yaml`. | **FR‑002**, **FR‑013**, **VI**, **plan_consistency‑e40c4d1b** |
| **3. Power Analysis** | • Estimate effect size for R² ≥ 0.6 → Cohen’s f². <br>• Use `statsmodels.stats.power.FTestPower` (α = 0.05, power = 0.8). <br>• Record required N and achieved power in `output/power_analysis.json`. <br>• Abort if actual N < required N. | **FR‑015**, **FR‑022**, **FR‑023**, **SC‑009** |
| **4. Train‑Test Split & VIF** | • Fixed seed `42`; 80/20 split → `data/train.parquet`, `data/test.parquet`. <br>• Compute VIF (statsmodels) on training descriptors. <br>• Drop descriptors with VIF > 5; log actions in `output/vif_summary.json`. | **FR‑016**, **SC‑010**, **FR‑013** |
| **5. Model Training** | • RandomForestRegressor (`n_estimators=500`, `max_features='sqrt'`). <br>• 5‑fold CV on training set; store CV scores. <br>• Persist model `output/rf_model.joblib`. | **FR‑003**, **FR‑013**, **VII** |
| **6. Descriptor‑Target Correlation (Training)** | • Pearson r & two‑tailed p for each descriptor (training data). <br>• Flag descriptors with |r| > 0.5 & p < 0.01. <br>• Save to `output/descriptor_corr.json`. | **FR‑014**, **SC‑007** |
| **7. External Validation Data** | • Perform a second API query with a different date range / filter to obtain an independent set (`data/hea_external.jsonl`). <br>• Validate and compute descriptors as in Steps 1‑2. | **FR‑017**, **FR‑018** (validation of external data) |
| **8. Performance Evaluation (Test Set)** | • Predict on held‑out test set. <br>• Compute R², Pearson r, p‑value; bootstrap confidence interval (sufficient resamples). <br>• Validate `output/metrics.json` against `contracts/metrics.schema.yaml`. | **FR‑004**, **SC‑001**, **SC‑002**, **SC‑003**, **VII**, **plan_consistency‑6579cb9c** |
| **9. Permutation Importance** | • Use `sklearn.inspection.permutation_importance` with a sufficient number of permutations per feature on test set. <br>• Perform non‑parametric permutation test; apply Holm‑Bonferroni (α = 0.05). <br>• Save to `output/perm_importance.json` and validate against `contracts/importance.schema.yaml`. | **FR‑005**, **FR‑006**, **SC‑003**, **plan_consistency‑3dd5d718** |
| **10. Stability Assessment** | • Repeat Phases 4‑9 three times with seeds `[111, 222, 333]`. <br>• Record the highest‑ranked feature rankings per run in `output/stability_rankings.json`.. <br>• Compute max rank difference; abort if > 1. | **FR‑021**, **SC‑006** |
| **11. Provenance & Reporting** | • Assemble `report.md` with sections: dataset stats, VIF, power analysis, descriptor‑target correlations, model performance (including CI), permutation importance (with corrected p‑values), stability results, **measurement‑protocol documentation for primary and external datasets**, and a provenance log. <br>• Generate `manifest.json` and validate against `contracts/manifest.schema.yaml`. | **FR‑008**, **FR‑010**, **FR‑019**, **SC‑004**, **SC‑011**, **FR‑024**, **plan_consistency‑49c0a31b** |
| **12. Contract Validation (FR‑018)** | • Run `jsonschema` validation on **all** generated artifacts: raw dataset, descriptor table, VIF summary, metrics, importance, stability rankings, manifest, runtime summary. <br>• Halt pipeline on any validation failure. | **FR‑018** |
| **13. CI Integration** | • GitHub Actions workflow (`.github/workflows/ci.yml`) runs all steps, validates contracts, lints (`ruff` ≤ 5 warnings) and formats (`black --check`). <br>• Writes `output/pipeline_runtime.json` with status, total runtime, and resource usage. | **T117‑T124** (future implementation) |

All phases are ordered so that data is acquired before any consumption, models are trained before evaluation, and figures/tables are generated before being embedded in the final report.
