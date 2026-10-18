# Implementation Plan: Predicting Molecular Halide Binding Affinities

**Branch**: `001-predicting-halide-binding-affinities` | **Date**: 2024-10-18 | **Spec**: `specs/001-predicting-halide-binding-affinities/spec.md`  
**Input**: Feature specification from `/specs/001-predicting-halide-binding-affinities/spec.md`

## Summary
The project builds a reproducible ML pipeline that predicts halide binding affinities for host molecules. Because open, directly‑downloadable experimental halide‑binding datasets are unavailable, the pipeline:

1. **Attempts** to scrape NIST Chemistry WebBook and PubChem (FR‑001), with all scrape failures handled defensively so the script never exits non‑zero on expected unavailability.
2. **Falls back** to an open SMILES dataset (verified HuggingFace URL) and **generates** a **primary simulated** dataset following FR‑011 (log K = 0.5 × charge_density + 0.3 × cavity_volume + N(0, 0.2)) for the single most abundant halide.
3. **Generates** an **independent evaluation** dataset where binding constants are drawn from a feature‑independent normal distribution N(0, 1), breaking the circularity of the primary simulation.
4. Computes RDKit descriptors & ECFP4 fingerprints (FR‑002).
5. Trains Random Forest and Gradient Boosting models with host‑molecule GroupKFold (FR‑004, FR‑005).
6. Performs bootstrap feature‑stability analysis and the FR‑013 physical plausibility check **always**; in Simulated mode the check result is recorded with an explicit "trivially satisfied by construction (simulated data)" annotation rather than skipped.
7. Generates partial dependence plots for the two most stable features (FR‑007).
8. Produces per‑halide R²/RMSE, bootstrap confidence intervals for pairwise performance differences, and a final report with an explicit associational disclaimer (FR‑008, FR‑009, FR‑012), followed by an appended independent‑evaluation section.

All steps are CPU‑only and fit within GitHub Actions free‑tier limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `pyyaml`, `jsonschema`, `seaborn`, `matplotlib`, `pyarrow`  
- **Storage**: CSV/JSON files under `data/`  
- **Testing**: `pytest` (unit tests for each script)  
- **Target Platform**: Linux (`ubuntu-latest` runner) – 2 vCPU, 7 GB RAM, ≤6 h runtime  
- **Constraints**: No GPU; deterministic RNG (`seed=42`) for all stochastic steps; strict host‑molecule split; per‑halide evaluation (Principle VI)  

## Constitution Check
| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| **I. Reproducibility** | Pin random seeds; fetch external data from canonical URLs. | All scripts set `RANDOM_SEED = 42`. Data ingestion uses verified HuggingFace URLs; scraping logic is deterministic with retries and defensive exception handling. |
| **II. Verified Accuracy** | All citations must be verified. | Task **T010** runs the Reference‑Validator Agent on every URL listed in `research.md`; CI blocks on failure. |
| **III. Data Hygiene** | Checksums, no in‑place mutation. | `utils.compute_checksum()` records SHA‑256 for every raw and processed file; new files are written for each transformation. |
| **IV. Single Source of Truth** | Figures/statistics trace to one data row and one code block. | Each metric is computed directly from `data/processed/halide_binding_data.csv`; reports reference the exact script and line numbers. |
| **V. Versioning Discipline** | Artifact hashes updated on change. | `Advancement-Evaluator` updates `state.yaml` with content hashes after each script finishes; T009 exercises `model_output.schema.yaml` against real output. |
| **VI. Halide‑Specific Evaluation** | Report per‑halide R²/RMSE. | Real‑data mode outputs per‑halide metrics; simulated single‑halide mode sets `comparative_analysis_aborted: true`. |
| **VII. Molecular Split Validation** | Split by host ID, not measurement. | `GroupKFold(groups=host_id)` guarantees no host appears in both train and test folds; verified by unit test before training. |

## Project Structure
```text
specs/001-predicting-halide-binding-affinities/
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
│   │   └── (scraped HTML or placeholder)
│   └── processed/
│       ├── halide_binding_data.csv
│       ├── independent_eval.csv
│       ├── model_runs.json
│       ├── feature_analysis.json
│       ├── figures/
│       │   ├── pdp_feature1.png
│       │   └── pdp_feature2.png
│       └── report.md
├── tests/
│   ├── test_data_ingestion.py
│   ├── test_model_split.py
│   ├── test_statistical_reporting.py
│   └── test_schema_validation.py
├── state.yaml
└── requirements.txt
```

**Structure Decision**: A single‑project layout keeps the pipeline lightweight and aligns with the CI runner’s filesystem constraints.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Simulated fallback (FR‑011)** | Open halide‑binding data are unavailable; fallback ensures a complete pipeline. | Dropping fallback would cause a hard failure, violating the requirement to produce a report. |
| **Host‑molecule GroupKFold** | Prevents data leakage; required by Constitution Principle VII. | Random split would inflate performance metrics and breach the constitution. |
| **Bootstrap CI (FR‑009)** | Wilcoxon invalid for N=5 folds; bootstrap provides robust CIs on small samples. | Parametric tests would assume normality and be statistically unsound. |
| **Physical Plausibility Check (FR‑013)** | Required unconditionally by the spec; always executed, with a construction‑triviality annotation in Simulated mode. | Skipping the check in Simulated mode would silently violate a MUST requirement. |
| **Partial Dependence Plots (FR‑007)** | Required by FR‑007 for interpretability. | Omitting PDPs would leave the requirement unsatisfied. |
| **Schema Validation (T009)** | Ensures contract compliance per Constitution Principle V. | Skipping validation could let mismatched outputs pass unnoticed. |
| **Citation Verification (T010)** | Satisfies Principle II on verified accuracy. | Assuming citations are correct without verification would breach the constitution. |
| **Independent Evaluation Set** | Breaks circularity of the primary simulated target (methodology‑f4c7012e, scientific_soundness‑f0482303). | Relying solely on the formula‑based simulation would inflate performance artificially. |
| **Defensive ingestion (T001a/T001b)** | Guarantees `01_data_ingestion.py` exits 0 on the CI runner even when scraping fails (re‑plan trigger). | A brittle scraper caused a non‑zero exit and unverifiable artifacts. |

## Implementation Tasks (mapping FR/SC)

| Task ID | Description | FR/SC Covered | Output |
|---------|-------------|---------------|--------|
| **T001a**: Scrape Attempt (defensive) | Attempt to scrape NIST/PubChem with `requests` (2 s delay, exponential backoff, max 5 retries) and `BeautifulSoup` HTML parsing. **Every network/parse error is caught and logged**; the scrape result (possibly empty) is written to `data/raw/scrape_result.csv`. The script never exits non‑zero due to scrape failure. | FR‑001 | `data/raw/scrape_result.csv` |
| **T001b**: Fallback Simulation (deterministic) | If the scrape yields <50 hosts with ≥3 halides: (1) log the exact FR‑011 warning; (2) identify the most abundant halide in the scraped data (default `Cl-` if scrape is empty); (3) load the verified SMILES parquet via `pandas.read_parquet` (with explicit column check and graceful error handling), sample 200 molecules (seed 42); (4) compute `charge_density` (sum of Gasteiger charges) and `cavity_volume` (RDKit molecular volume) and generate the **single‑halide** primary simulated set: `logK = 0.5*charge_density + 0.3*cavity_volume + rng.normal(0, 0.2)`; (5) generate the **independent evaluation set** of 100 additional molecules with `logK = rng.normal(0, 1)` (feature‑independent); (6) apply the solvent filter and the ≥3‑halide retention rule **only to real scraped data** — in Simulated mode each host carries exactly one halide measurement by construction, so the ≥3‑halide filter is not applicable and is skipped with a logged note; (7) write `halide_binding_data.csv` and `independent_eval.csv` and validate both against `contracts/dataset.schema.yaml` before use (FR‑011 step 4). | FR‑001, FR‑010, FR‑011, SC‑005 | `data/processed/halide_binding_data.csv`, `data/processed/independent_eval.csv` |
| **T002**: Feature Engineering | Compute ECFP4 (radius 2, 1024 bits) and a suite of RDKit descriptors (MolWt, LogP, TPSA, etc.). Standardize continuous descriptors (z‑score). Append columns to a new CSV file. | FR‑002, SC‑002 | Updated `halide_binding_data.csv` |
| **T003**: Power Check per Halide | Count hosts per halide; if any halide has <10 hosts, set `underpowered: true` in `metadata.json` and flag wide CIs later. | FR‑012, SC‑006 | `data/processed/metadata.json` |
| **T004**: Model Training (Real‑Data Mode) | Train Random Forest and Gradient Boosting with 5‑fold `GroupKFold` (group=`host_id`). Record per‑fold R² and RMSE; compute mean ± std. Store results in `model_runs.json` using the **`metrics` object** (`r2_mean`, `r2_std`, `rmse_mean`, `rmse_std`) plus a `fold_metrics` list, exactly matching `contracts/model_output.schema.yaml`. | FR‑004, FR‑005, SC‑001, SC‑003 | `model_runs.json` |
| **T005**: Model Training (Simulated‑Data Mode) | Same as T004 but on the **single‑halide** simulated set; `data_mode: Simulated`. | FR‑011, SC‑001 | `model_runs.json` |
| **T006**: Feature Stability & Physical Plausibility Check | Bootstrap (1000 resamples) feature importance; compute CV; flag CV ≥ 0.3 as unstable. **Always perform** the FR‑013 physical plausibility check on the sign of the top feature (`charge_density`): in Real mode report the check outcome; in Simulated mode report the outcome with the explicit annotation "trivially satisfied by construction (simulated data)" so the check is executed, not skipped. | FR‑006, FR‑013, SC‑002, SC‑007 | `feature_analysis.json` |
| **T007**: Partial Dependence Plots | Using `sklearn.inspection.PartialDependenceDisplay`, generate PDPs for the two most stable features (e.g., `charge_density`, `cavity_volume`). Save PNGs to `figures/`. | FR‑007 | `figures/pdp_*.png` |
| **T008**: Statistical Reporting | If `data_mode: Real` and ≥2 halides and not underpowered, compute **pairwise bootstrap 95 % CIs** (10 000 resamples) for ΔR² and ΔRMSE; otherwise set `comparative_analysis_aborted: true`. Include associational disclaimer and under‑power warnings. Generates `report.md`. | FR‑008, FR‑009, FR‑012, SC‑005, SC‑007 | `report.md` |
| **T009**: Model Output Schema Validation | Run `python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml`. Fail pipeline on mismatch. | Contract compliance (Principle V) | Validation log |
| **T010**: Citation Verification | Invoke the Reference‑Validator Agent on all URLs listed in `research.md`. CI will block if any citation fails verification. | Principle II | Verification log |
| **T011**: Independent Evaluation on Hold‑Out Set | Load `independent_eval.csv`, compute predictions using the trained models, evaluate R²/RMSE, and **append** a dedicated section to the existing `report.md` (does not regenerate it). This demonstrates performance on a target that is not a deterministic function of the descriptors. | Scientific robustness (methodology‑f4c7012e) | Appended section in `report.md` |

All tasks are ordered so that data download precedes any consumption, models are trained before analysis, figures are generated before the report references them, and the independent‑evaluation section is appended after the report is generated (T008 → T011).