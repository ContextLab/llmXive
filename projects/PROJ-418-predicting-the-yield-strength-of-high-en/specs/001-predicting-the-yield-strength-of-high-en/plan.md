# Implementation Plan: Predicting the Yield Strength of High‑Entropy Alloys

**Branch**: `feature/predict-hea-yield-strength` | **Date**: 2026‑08‑23 | **Spec**: [spec.md](../specs/feature/predict-hea-yield-strength/spec.md)  
**Input**: Feature specification from `/specs/feature/predict-hea-yield-strength/spec.md`

## Summary
Develop an end‑to‑end CPU‑first pipeline that (1) downloads the curated HEA yield‑strength dataset, (2) validates and deduplicates the data, (3) computes deterministic composition‑based descriptors, (4) splits a **[deferred]** held‑out test set before any cross‑validation, (5) trains a Random Forest regressor with **5‑fold cross‑validation**, (6) evaluates on the held‑out test set reporting R², Pearson r and associated p‑value, (7) computes permutation importance with exactly **1000 permutations** per feature, (8) assesses importance significance via a non‑parametric permutation test (α = 0.05) with Bonferroni correction, (9) generates a reproducibility **manifest.json** recording required provenance fields and validates it against a dedicated schema, (10) produces a comprehensive `report.md` with all mandated sections, (11) validates every intermediate artifact against its JSON schema contract, (12) checks that all success criteria are met, (13) runs linting (`ruff` ≤ 5 warnings) and formatting (`black --check`), and (14) generates a `README.md` with usage instructions and ensures inline code comments throughout the codebase. All functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑008) are explicitly addressed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==2.0.*`, `scikit‑learn==1.5.*`, `scipy==1.14.*`, `matplotlib==3.9.*`, `jsonschema==4.23.*`, `ruff==0.6.*`, `black==24.*`  
- **Storage**: File‑based CSV/JSON under `data/` and `output/`  
- **Testing**: `pytest==8.*` with contract validation via `jsonschema`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ≈ 7 GB RAM) – CPU‑first; no GPU required.  
- **Performance Goals**: End‑to‑end runtime ≤ 7200 s on an 8‑core CPU; ≤ 5 ruff warnings.  
- **Constraints**: Fixed permutation count = 1000 (FR‑012); no adaptive counts.

## Constitution Check
| Principle | Satisfied? | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | All seeds, versions, and checksums recorded in `manifest.json`. |
| II. Verified Accuracy | ✅ | All citations are drawn from verified URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | ✅ | Raw data checksummed; transformations write new files with documented derivation. |
| IV. Single Source of Truth | ✅ | `data/processed/hea_processed.parquet` is designated as the SSoT for all downstream analyses. |
| V. Versioning Discipline | ✅ | All artifacts hashed; `state/projects/...yaml` updated automatically by CI. |
| VI. Deterministic Descriptor Engineering | ✅ | Descriptor functions live in `code/descriptors.py` and are version‑controlled. |
| VII. Statistical Rigor and Uncertainty Quantification | ✅ | 5‑fold CV, bootstrap CIs (≥ 1000 resamples), permutation importance with exact 1000 permutations, and full seed logging. |

## Project Structure
```
specs/feature/predict-hea-yield-strength/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── descriptor.schema.yaml
    ├── elemental_properties.schema.yaml
    ├── hea_composition.schema.yaml
    ├── hea_schema.schema.yaml
    ├── importance.schema.yaml
    ├── metrics.schema.yaml
    ├── metrics_schema.schema.yaml
    ├── model_metrics.schema.yaml
    ├── model_output.schema.yaml
    ├── output.schema.yaml
    ├── performance.schema.yaml
    ├── processed_data.schema.yaml
    ├── runtime.schema.yaml
    └── manifest.schema.yaml   ← **new contract**
```

## Complexity Tracking
No constitution violations remain; the data model now defines entities required by the contract schemas (FR‑007).

## Phase‑wise Implementation Plan

| Phase | Description | FR/SC addressed | Output / Contract |
|-------|-------------|----------------|-------------------|
| **1. Data Acquisition** | Download dataset from Zenodo, verify SHA‑256, store under `data/raw/`. | FR‑001, FR‑013, SC‑005 | `data/raw/hea_yield_strength.csv` validated against `dataset.schema.yaml` |
| **2. Validation & Deduplication** | Validate each row against `dataset.schema.yaml`; abort on missing fields (FR‑009). Remove duplicate rows, **log the number removed** (FR‑014). Abort if any element not in `elemental_properties.schema.yaml` (FR‑015). | FR‑009, FR‑014, FR‑015, SC‑005 | Log file `output/deduplication.log`; validated CSV written to `data/processed/hea_clean.csv` |
| **3. Descriptor Calculation** | Compute deterministic descriptors using `code/descriptors.py` (VI). Validate against `descriptor.schema.yaml`. Compute VIFs; if any VIF > 10, **drop the highest‑VIF feature**, retrain a secondary model, and report both. | FR‑002, VI, SC‑006 (stability reporting) | `data/processed/hea_descriptors.parquet` validated against `descriptor.schema.yaml` |
| **4. Train‑Test Split** | Randomly reserve **[deferred]** of clean data as held‑out test set **before** any CV (Methodology‑d900b98b). Remaining portion used for 5‑fold CV (k=5). | FR‑003, SC‑001, SC‑002 | Split files `data/processed/train.parquet`, `data/processed/test.parquet` |
| **5. Model Training** | Fit Random Forest (n_estimators=500, max_depth=None) on CV training folds. Store hyperparameters. | FR‑003, FR‑010, SC‑004 | `output/model.pkl` |
| **6. Performance Evaluation** | Predict on held‑out test set; compute R², Pearson r, two‑tailed p‑value. **Assert R² ≥ 0.6 (SC‑001) and |r| ≥ 0.5 (SC‑002)**. | FR‑004, SC‑001, SC‑002 | `output/metrics.json` validated against `metrics.schema.yaml` |
| **7. Permutation Importance** | Perform a substantial number of permutations per feature on the test set. (FR‑005, FR‑012). Compute mean/std and raw p‑values; apply **Bonferroni correction** (SC‑003). **Assert all corrected p < 0.05** for flagged features. | FR‑005, FR‑006, SC‑003 | `output/importance.json` validated against `importance.schema.yaml` |
| **8. Bootstrap Uncertainty** | Bootstrap R² and Pearson r (≥ 1000 resamples) to obtain 95 % CIs (VII). | VII | Added to `output/metrics.json` |
| **9. Manifest Generation** | Populate `manifest.json` with **pipeline_version, run_timestamp, random_seeds (data_split, model, bootstrap), software_versions, data_checksums, artifact_checksums, git_commit**. Validate against the new `manifest.schema.yaml`. **Abort if any required field is missing**. | FR‑007, SC‑007 | `output/manifest.json` (validated against `manifest.schema.yaml`) |
| **10. Report Generation** | Assemble `report.md` containing dataset statistics, VIF summary, model performance, importance tables (with corrected p‑values), bootstrap CIs, **top‑5 feature stability across three independent runs (≤ 1 rank difference, SC‑006)**, and mandatory disclaimer. | FR‑008, SC‑006, SC‑008 | `output/report.md` |
| **11. README & Code Comments** | Generate `README.md` with usage instructions, dependency list, and execution steps. Ensure all source files contain inline comments; enforce via a custom `ruff` rule check. | FR‑011 | `README.md`, lint passes |
| **12. Lint & Formatting** | Run `ruff` (≤ 5 warnings) and `black --check` (0 errors). Fail pipeline if thresholds exceeded (SC‑008). | SC‑008 | Lint log `output/lint_report.txt` |
| **13. Runtime Check** | Record wall‑clock time; **assert total ≤ 7200 s** (SC‑004). | SC‑004 | `output/pipeline_runtime.json` validated against `runtime.schema.yaml` |
| **14. Contract Validation** | After each artifact creation, run `jsonschema.validate` against **all contracts** in `contracts/` (including the new `manifest.schema.yaml`). Abort on validation failure. | FR‑013, SC‑005 | Validation logs `output/contract_validation.log` |
| **15. Stability Analysis** | Repeat the full pipeline **three times** with different seeds, collect top‑5 feature rankings, compute rank differences, and write `output/stability_rankings.json`. | SC‑006 | `output/stability_rankings.json` validated against `performance.schema.yaml` |
| **16. Traceability Matrix** | Document mapping of every FR and SC to the above phases (see matrix below). | All FR/SC | Included in this plan document. |

### Traceability Matrix

| FR / SC | Mapped Phase |
|---------|--------------|
| FR‑001 | Phase 1 |
| FR‑002 | Phase 3 |
| FR‑003 | Phase 4 |
| FR‑004 | Phase 6 |
| FR‑005 | Phase 7 |
| FR‑006 | Phase 7 |
| FR‑007 | Phase 9 |
| FR‑008 | Phase 10 |
| FR‑009 | Phase 2 |
| FR‑010 | Phase 12 |
| FR‑011 | Phase 11 |
| FR‑012 | Phase 7 (assertion) |
| FR‑013 | Phase 14 |
| FR‑014 | Phase 2 |
| FR‑015 | Phase 2 |
| SC‑001 | Phase 6 (post‑eval check) |
| SC‑002 | Phase 6 (post‑eval check) |
| SC‑003 | Phase 7 (Bonferroni) |
| SC‑004 | Phase 13 |
| SC‑005 | Phase 2 & Phase 14 |
| SC‑006 | Phase 15 |
| SC‑007 | Phase 9 |
| SC‑008 | Phase 12 & Phase 14 |

## Contract Validation Table
| Phase | Artifact(s) Produced | JSON Schema(s) Validated |
|-------|----------------------|---------------------------|
| 1 | `data/raw/hea_yield_strength.csv` | `dataset.schema.yaml` |
| 2 | `data/processed/hea_clean.csv` | `dataset.schema.yaml` (post‑validation) |
| 3 | `data/processed/hea_descriptors.parquet` | `descriptor.schema.yaml` |
| 4 | `data/processed/train.parquet`, `data/processed/test.parquet` | `hea_composition.schema.yaml` (structure of split files) |
| 5 | `output/model.pkl` | *No schema* (binary artifact) |
| 6 | `output/metrics.json` | `metrics.schema.yaml`, `performance.schema.yaml` |
| 7 | `output/importance.json` | `importance.schema.yaml` |
| 8 | (augmented `output/metrics.json`) | `metrics.schema.yaml` (updated) |
| 9 | `output/manifest.json` | **`manifest.schema.yaml`** (new) |
| 10 | `output/report.md` | *No JSON schema* (human‑readable) |
| 11 | `README.md` | *No schema* |
| 12 | `output/lint_report.txt` | *No schema* |
| 13 | `output/pipeline_runtime.json` | `runtime.schema.yaml` |
| 14 | `output/contract_validation.log` | *No schema* (log) |
| 15 | `output/stability_rankings.json` | `performance.schema.yaml` |
| 16 | Traceability matrix (in this plan) | *No schema* |

## Additional Notes
- **SSoT Designation**: `data/processed/hea_processed.parquet` is the single source of truth for all downstream steps and is recorded in the manifest.
- **Fixed Permutation Count Enforcement**: The permutation routine is hard‑coded to `n_permutations=1000`; a unit test asserts this constant.
- **External Validation**: After the primary evaluation, the model is applied to the Open Materials Database HEA subset and results are logged (not a success‑criterion but an additional robustness check).
