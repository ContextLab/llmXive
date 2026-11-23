# Implementation Plan: Predicting Molecular Halide Binding Affinities

**Branch**: `001-predicting-halide-binding-affinities` | **Date**: 2024-10-24 | **Spec**: `specs/001-predicting-molecular-halide-binding-affi/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-molecular-halide-binding-affi/spec.md`

## Summary
We will build a reproducible, CPU‑only machine‑learning workflow that (1) attempts to scrape experimental halide binding constants from NIST Chemistry WebBook and PubChem (FR‑001); if the scrape yields fewer than 50 host molecules with ≥3 halide measurements, the pipeline **automatically switches** to a deterministic simulated dataset (FR‑011) **and explicitly aborts the comparative analysis** (the primary research question cannot be answered with simulated data). (2) generates molecular fingerprints, RDKit descriptors, **and one‑hot encodes halide identity** as predictor features (FR‑002, methodology‑d455a955). (3) trains Random Forest and Gradient Boosting models with host‑molecule GroupKFold cross‑validation (FR‑004, FR‑005) and logs runtime and peak RAM to `training_log.json` (SC‑003, spec_coverage‑fc2188ce). (4) conducts bootstrap feature‑stability analysis and a physical plausibility check (FR‑006, FR‑013). (5) produces partial‑dependence plots for at least two key features (FR‑007). (6) reports per‑halide R²/RMSE with **bootstrap confidence intervals** (10 000 resamples) **only when each halide has ≥20 hosts**; otherwise the CI step is aborted and a “wide‑CI / under‑powered” warning is emitted (FR‑009, methodology‑0770c9cb). (7) validates all JSON artifacts against their schemas, including a new validation step for `output_summary.json` (Task T014, methodology‑baa04c9d). (8) aggregates all results into **`results_master.json`**, the designated Single Source of Truth (SSoT) for the project (principle VII, plan_consistency‑dafda843). (9) performs a genuine external evaluation using an independent RDKit descriptor dataset (logP values) instead of random noise (methodology‑eb8b2366). All steps are ordered so that data download precedes consumption, models are trained before analysis, figures are generated before they are referenced in the report, and the independent‑evaluation step runs **after** the main report is generated (it appends to the file).  

All tasks run on the GitHub Actions free‑tier runner; no GPU escape hatch is required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `pyyaml`, `jsonschema`, `seaborn`, `matplotlib`, `pyarrow`  
- **Storage**: CSV/JSON files under `data/processed/`  
- **Testing**: `pytest` (tests live in top‑level `tests/` directory)  
- **Target Platform**: Linux (`ubuntu-latest`) on GitHub Actions free tier (2 vCPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: Deterministic RNG (`seed=42`), A brief request delay with exponential backoff, no in‑place data mutation, SHA‑256 artifact hashing after every write.  

## Constitution Check
| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| **I. Reproducibility** | Pin seeds; deterministic scripts; same external URLs each run. | All scripts set `RANDOM_SEED = 42`; data ingestion uses the verified URLs listed in `research.md`. |
| **II. Verified Accuracy** | All citations must be validated. | `research.md` cites only the verified URLs from the “Verified Datasets” block; Reference‑Validator Agent runs automatically. |
| **III. Data Hygiene** | Checksums; no in‑place mutation. | `utils.compute_checksum()` records SHA‑256 for each raw and processed file; every transformation writes a new file. |
| **IV. Single Source of Truth** | Every figure, statistic, or interpretation must trace back to exactly one data row and one code block. | **`results_master.json`** is the designated SSoT; all metrics, figures, and tables are derived from keys in this file; each figure script writes a comment linking back to the JSON key. |
| **V. Versioning Discipline** | Content hash for every artifact. | Task **T012** invokes the Advancement‑Evaluator after each artifact write, updating `state.yaml`. |
| **VI. Halide‑Specific Evaluation** | Report per‑halide R²/RMSE. | `model_runs.json` stores per‑halide metrics; `results_master.json` aggregates them; `report.md` contains per‑halide tables (or abort flag). |
| **VII. Molecular Split Validation** | Split by host molecule identity. | `RepeatedGroupKFold(groups=host_id)` guarantees no host appears in both train and test within a fold; unit test `tests/test_model_split.py` verifies this. |

## Project Structure
```text
specs/001-predicting-molecular-halide-binding-affi/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── output.schema.yaml

projects/PROJ-446-predicting-molecular-halide-binding-affi/
├── code/
│   ├── 01_data_ingestion.py
│   ├── 02_feature_engineering.py
│   ├── 03_model_training.py
│   ├── 04_feature_analysis.py
│   ├── 05_statistical_reporting.py
│   ├── 06_partial_dependence.py
│   ├── 07_independent_evaluation.py
│   └── utils.py
├── data/
│   ├── raw/
│   │   └── (scrape artefacts, optional placeholder)
│   └── processed/
│       ├── halide_binding_data.csv
│       ├── independent_eval_logp.csv
│       ├── model_runs.json
│       ├── feature_analysis.json
│       ├── training_log.json
│       ├── results_master.json
│       ├── figures/
│       │   ├── pdp_charge_density.png
│       │   └── pdp_cavity_volume.png
│       ├── report.md
│       └── output_summary.json
├── tests/
│   ├── test_data_ingestion.py
│   ├── test_feature_engineering.py
│   ├── test_model_split.py
│   ├── test_statistical_reporting.py
│   └── test_schema_validation.py
├── state.yaml
└── requirements.txt
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Simulated fallback (FR‑011)** | No open experimental halide‑binding data; required to produce any output. | Dropping fallback would cause a hard failure, violating the specification. |
| **RepeatedGroupKFold (a set of folds)** | Increases effective sample size for bootstrap CI, addressing the “scientific_soundness‑eb109c00” concern. | Simple 5‑fold would give too few points for reliable CI. |
| **Bootstrap CI (FR‑009)** | Wilcoxon is disallowed; bootstrap provides robust intervals for small N. | Parametric tests would assume normality and be unsound. |
| **Physical Plausibility Check (FR‑013)** | Required unconditionally; even in simulated mode we must record it. | Skipping would violate a MUST requirement. |
| **Partial Dependence Plots (FR‑007)** | Needed for interpretability. | Omitting PDPs would leave FR‑007 unsatisfied. |
| **Schema Validation (Task T009, T014)** | Guarantees contract compliance (Principle V). | Skipping validation could let mismatched outputs pass unnoticed. |
| **Citation Verification (Task T010)** | Reference‑Validator Agent enforces Principle II. | Assuming citations are correct without verification would breach the constitution. |
| **Defensive ingestion (Tasks T001a/T001b)** | Guarantees CI does not error out on expected missing data. | A brittle scraper would cause non‑zero exit and block the pipeline. |
| **Independent evaluation (methodology‑f4c7012e)** | Demonstrates model does not achieve artificially high performance on a target unrelated to the features. | Relying solely on the deterministic simulated target would inflate performance artificially. |
| **Advancement‑Evaluator Hash Recording (Task T012)** | Records SHA‑256 hashes per Constitution Principle V. | Omitting would leave hash updates undocumented. |
| **Training runtime logging (Task T013)** | Record wall‑clock time and peak RAM to satisfy SC‑003. | Without this metric the runtime budget cannot be verified. |
| **Master results SSoT (Task T016)** | Provide a concrete single source of truth for all downstream artifacts (Principle VII). | Without a named SSoT artifact the requirement is ambiguous. |

All tasks are ordered so that data download precedes consumption, models are trained before analysis, figures are generated before they are referenced, and the independent‑evaluation step runs **after** the main report is generated (it appends to the file).  

## Implementation Tasks (Mapping FR/SC → Outputs)

| Task ID | Description | FR/SC Covered | Output |
|---------|-------------|---------------|--------|
| **T001a** | Scrape NIST WebBook & PubChem with `requests` (2 s delay, exponential backoff, max a limited number of retries). All errors caught, script exits `0`. Writes `data/raw/scrape_result.csv`. | FR‑001 | `data/raw/scrape_result.csv` |
| **T001b** | If `<50` hosts with ≥3 halides, log FR‑011 warning, identify most abundant halide (default `Cl-`), load SMILES parquet (`https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet`). Sample with seed 42. Compute simulated `logK = 0.5*charge_density + 0.3*sqrt(cavity_volume) + 0.2*charge_density*cavity_volume + N(0,0.3)`. Write `halide_binding_data.csv`. Validate against `contracts/dataset.schema.yaml`. **Mark comparative analysis as aborted** (the primary research question cannot be answered with simulated data). | FR‑001, FR‑010, FR‑011, SC‑005 | `data/processed/halide_binding_data.csv` |
| **T002** | Compute ECFP4 (radius 2, 1024 bits), RDKit descriptors, **one‑hot encode halide_identity** (4 binary columns). Standardize continuous descriptors (z‑score). Write updated CSV. Unit test `tests/test_feature_engineering.py` imports via `sys.path.append('code')`. | FR‑002, methodology‑d455a955 | Updated `halide_binding_data.csv` |
| **T003b** | Filter to retain only host molecules with ≥3 distinct halide measurements (F⁻, Cl⁻, Br⁻, I⁻). Log retained/excluded counts. | FR‑003, SC‑004 | Filtered `halide_binding_data.csv` |
| **T003** | Count hosts per halide; if any halide `<10`, write `metadata.json` with `"underpowered": true` and `"underpowered_reason": "N < 10 per halide (minimum 20 required for stable bootstrap CI)"`. | FR‑012, methodology‑0770c9cb, SC‑006 | `data/processed/metadata.json` |
| **T004** | Train Random Forest & Gradient Boosting (default hyper‑parameters) using **RepeatedGroupKFold** (`n_splits=5`, `n_repeats=5`). Record per‑fold R²/RMSE, compute mean ± std, store in `model_runs.json` matching `contracts/model_output.schema.yaml`. | FR‑004, FR‑005, SC‑001, SC‑003 | `data/processed/model_runs.json` |
| **T005** | Same training pipeline on simulated single‑halide data; set `"data_mode": "Simulated"` in JSON. | FR‑011, SC‑001 | `model_runs.json` (additional entry) |
| **T006** | Bootstrap a large number of resamples; compute permutation importance per resample; calculate CV for each feature; flag CV ≥ 0.3 as unstable. Perform physical plausibility check on sign of `charge_density`. Write `feature_analysis.json`. | FR‑006, FR‑013, SC‑002, SC‑007 | `data/processed/feature_analysis.json` |
| **T007** | Generate Partial Dependence Plots for top‑2 stable features (`charge_density`, `cavity_volume`) using `sklearn.inspection.PartialDependenceDisplay`. Save PNGs in `figures/`. | FR‑007 | `figures/pdp_charge_density.png`, `figures/pdp_cavity_volume.png` |
| **T008** | **Bootstrap CI**: 10 000 resamples of per‑fold mean R²/RMSE differences for every halide pair **only if each halide has ≥20 hosts**. If under‑powered, abort CI and set `"aborted": true` with a wide‑CI warning. Report 95 % CI; flag “not statistically distinguishable” when CI includes zero. Include associational disclaimer; if under‑powered, note “wide CI”. Write `report.md` (human) and `output_summary.json` (machine) conforming to `contracts/output.schema.yaml`. | FR‑008, FR‑009, FR‑012, SC‑005, SC‑007 | `data/processed/report.md`, `data/processed/output_summary.json` |
| **T009** | Validate `model_runs.json` against `contracts/model_output.schema.yaml` via `jsonschema`. Fail pipeline on mismatch. | Contract compliance (Principle V) | Validation log (CI step) |
| **T010b** | Wrapper for **RepeatedGroupKFold** to produce 25 folds, feeding the bootstrap CI step. | Scientific rigor (addressing concern scientific_soundness‑eb109c00) | No new file; influences `model_runs.json` and CI |
| **T010** | Reference‑Validator Agent automatically checks all URLs listed in `research.md`. CI blocks on failure. | Principle II | Verification log (CI step) |
| **T011** | Load `independent_eval_logp.csv` (logP values from RDKit parquet `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet`), predict with trained models, compute R²/RMSE, **append** a dedicated “Independent Evaluation (logP)” section to existing `report.md`. Demonstrates non‑circular benchmark. | methodology‑eb8b2366 | Updated `report.md` (appended section) |
| **T012** | After each artifact write (CSV, JSON, PNG, Markdown), invoke Advancement‑Evaluator to compute SHA‑256 hash and update `state.yaml` under `artifacts`. Ensures compliance with Constitution Principle V. | Constitution V | Updated `state.yaml` (not shown) |
| **T013** | Record wall‑clock training time and peak RAM usage (via `psutil`) to `training_log.json`; validate against a tiny schema (not shown) to satisfy SC‑003. | SC‑003 | `data/processed/training_log.json` |
| **T014** | Validate `output_summary.json` against `contracts/output.schema.yaml` using `jsonschema`. | FR‑014, plan_consistency‑baa04c9d | Validation log (CI step) |
| **T015** | Load external RDKit descriptor parquet (`https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet`), extract `logP` as target, evaluate models, and report results in the independent‑evaluation section (replaces random noise). | methodology‑eb8b2366 | Updated `report.md` section |
| **T016** | Aggregate per‑halide metrics, feature‑stability ranking, bootstrap CI results, and training logs into `results_master.json`. All downstream figures and tables reference keys in this file, satisfying the Single Source of Truth requirement. | Constitution VII, plan_consistency‑dafda843 | `data/processed/results_master.json` |

All tasks respect the ordering: download → preprocess → filter → power check → model training → feature analysis → PDPs → statistical report → independent evaluation → schema validation → hash recording → master results aggregation.

## Decision Rationale: Compute & Data
- **Compute**: All modeling steps (≤ 200 samples in simulated mode, ≤ 5 × 5 = 25 CV folds) are trivially CPU‑tractable and comfortably fit the 7 GB RAM budget and ≤ 6 h runtime on the GitHub Actions free tier. No GPU escape hatch is needed.  
- **Data**: No open source provides the required experimental halide‑binding constants. The SMILES parquet is the only verified source containing valid molecular structures, satisfying the fallback requirement (FR‑011). All ingestion steps are defensive: expected failures are logged, never cause a non‑zero exit.  

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| No real binding data | High – primary comparative question unanswerable | FR‑011 fallback; clear flag in report; independent evaluation set to avoid circularity. |
| Ingestion script failure on CI | High – unverifiable artifacts | Defensive try/except, guaranteed exit 0, unit test `test_data_ingestion.py` ensures script runs without error. |
| Data leakage | High – inflated metrics | Enforced `RepeatedGroupKFold` by `host_id`; unit test `test_model_split.py` validates grouping before training. |
| Small per‑halide sample size | Medium – wide CIs | Bootstrap CI only when ≥20 hosts per halide; under‑power flag; no significance claims. |
| Descriptor collinearity | Medium – unstable importance | CV‑based stability; flag unstable features; report VIF diagnostics. |
| Trivial physical plausibility (simulated) | Low – check always runs | Annotate result as “trivially satisfied by construction (simulated data)”. |

---  