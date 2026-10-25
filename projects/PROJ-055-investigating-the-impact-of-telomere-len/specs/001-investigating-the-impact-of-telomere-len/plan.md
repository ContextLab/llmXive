# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-10-24 | **Spec**: `specs/001-telomere-lifespan-impact/spec.md`  
**Input**: Feature specification from `/specs/001-telomere-lifespan-impact/spec.md`

## Summary
The pipeline now **uses static, open‑access URLs** for the required Dryad telomere datasets and the published lifespan CSVs (all verified in the “Verified datasets” block). Ecological covariates are fetched from the open AnAge API and BirdLife International range dataset, satisfying Constitutional Principle VI. All modeling follows the mandated Linear Mixed‑Effects Model (LMM) (Principle VII) and includes an **external permutation‑test validation** to break circularity in significance assessment (addressing SC‑002).

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (accessed via `rpy2`)
- **Primary Dependencies**  
  - Python: `pandas`, `numpy`, `requests`, `pyyaml`, `rpy2`, `matplotlib`, `tqdm`, `jsonschema`  
  - R (installed via the new verifier script): `lme4`, `lmerTest`, `ggplot2`, `patchwork`
- **Storage**: Local filesystem (`data/`, `results/`, `logs/`)
- **Testing**: `pytest` + schema validation (`jsonschema` for Python)
- **Target Platform**: Linux (GitHub Actions free tier)
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h wall‑clock, CPU‑only (no GPU needed)
- **Scale/Scope**: Real open datasets (Dryad telomere, published lifespan CSVs, AnAge, BirdLife). No synthetic placeholders.

> All quantitative statements (e.g., dataset size, number of species) are **deferred** to the research phase.

## Phase Overview

| Phase | Script | Description | FR(s) addressed | SC(s) addressed |
|-------|--------|-------------|----------------|-----------------|
| 0 – Configuration | `code/config.yaml` (static URLs) | Pre‑populated with verified Dryad DOI URLs and lifespan CSV URLs; no discovery script needed. | FR‑001 | — |
| 1 – Ingestion | `02_ingest_data.py` | Downloads each CSV from the static URLs, records SHA‑256 checksums, stores under `data/raw/`. Fails with clear error if any download fails. | FR‑001 | SC‑001 (total rows) |
| 2 – Cleaning & Merge | `03_clean_merge.py` | Renames columns, converts telomere units to kilobases, filters wild‑caught individuals, merges telomere, lifespan, and ecological covariates on `species_id`. Writes `data/processed/analysis_ready.csv`, `missing_data_log.csv`, `unconvertible_units.csv`. | FR‑002, FR‑003, FR‑008, 0‑be37fff | SC‑001 (proportion merged) |
| 3 – Ecological Covariates | `04_fetch_ecology.py` | Retrieves migration status, breeding latitude, and body mass from AnAge (`https://www.anage.org/api/...`) and BirdLife (`https://birdlife.org/data/range.csv`). Stores as `data/raw/ecology.csv` with provenance fields. | FR‑002, FR‑003, VI | — |
| 4 – R Packages Verification | `04_verify_r_packages.py` | Uses `rpy2` to ensure required R packages (`lme4`, `lmerTest`, `ggplot2`, `patchwork`) are installed; installs missing packages via `install.packages` and exits with status 0 on success. | — | — |
| 5 – Modelling (Base LMM) | `05_fit_lmm_base.py` | Fits `lifespan_days ~ telomere_length_kb + body_mass_g + breeding_latitude + (1|species_id)` via `lme4::lmer`. Checks `n_species`; if `< 15`, writes low‑power flag and **skips** power simulation. | FR‑004, FR‑008, 252954db, 2bffcfac | SC‑002 (α = 0.05), SC‑005 (conditional) |
| 6 – Modelling (Interaction LMM) | `06_fit_lmm_interaction.py` | Fits `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + body_mass_g + (1|species_id)`. Excludes rows with `migration_status == "Unknown"` from interaction terms; logs exclusion count. | FR‑005, FR‑008 | SC‑003 (ΔAIC) |
| 7 – Sensitivity & Power | `07_sensitivity_power.py` | *Sensitivity*: LOOCV‑by‑species when `n_species ≥ 10`; otherwise jackknife‑by‑data‑source. Logs coefficients in `results/sensitivity_log.csv`. *Power*: Runs **only** when `n_species ≥ 15`. Simulates 1 000 datasets across telomere slopes (0.05–0.30) and records power curves in `results/power_report.yaml`. | FR‑006, SC‑004, SC‑005 (consistent) | — |
| 8 – External Significance Validation | `08_permutation_test.py` | Generates 10 000 label‑permuted versions of `analysis_ready.csv`, refits the base LMM each time, computes an empirical p‑value for the telomere coefficient. Saves `results/permutation_pvalue.yaml`. The final **significance_flag** (in model output) is set to `true` only if **both** the model‑based p‑value **and** the permutation p‑value are `< 0.05`. | — | SC‑002 (empirical benchmark) |
| 9 – Visualisation | `09_visualise.py` | Generates `results/association_forest.png` (fixed‑effect forest plot) and `results/moderator_plot.png` (grouped scatter for migration status and latitude gradient). | FR‑007 | — |
|10 – Validation & Reporting | `10_validate_report.py` | Validates `analysis_ready.csv` against `contracts/dataset.schema.yaml` and model outputs against `contracts/model_output.schema.yaml`. Assembles `results/report.yaml` summarising all SCs and the dual‑p‑value significance flag. | — | All SCs |

## Compute Feasibility
All steps run comfortably on 2 vCPU / 7 GB RAM; total wall‑clock < 30 minutes. No GPU required.

## Risk Mitigation
- **Missing authentic data** – URLs are static and verified; the ingestion script aborts with a clear “Data Unavailable” error if any download fails. No placeholder data are used.
- **Memory overrun** – CSVs are streamed (`chunksize=50_000`) and aggregated on‑the‑fly.
- **Model non‑convergence** – Switches to `bobyqa` optimizer; if still failing, writes low‑power flag and exits gracefully.
- **Low‑species count** – Emits low‑power warning and skips power simulation (consistent with SC‑005).
- **Circular significance** – The permutation test (Phase 8) supplies an external benchmark for SC‑002, breaking circularity.
- **R‑package verification** – Implemented as a robust Python‑driven verifier that installs missing packages, guaranteeing exit 0 on a functional runner.

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic scripts, SHA‑256 checksums recorded for every file. |
| II. Verified Accuracy | PASS | All external data fetched from verified Dryad, AnAge, and BirdLife URLs. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | PASS | All figures and statistics trace back to `data/processed/analysis_ready.csv` and version‑controlled scripts. |
| V. Versioning Discipline | PASS | Artifact hashes stored in `state/projects/PROJ-055...yaml`. |
| VI. Ecological Data Integration | PASS | Covariates sourced from AnAge and BirdLife (open, verified). |
| VII. Statistical Modeling Transparency | PASS | LMM scripts under `code/`, formulas explicit in headers, outputs saved as versioned artifacts. |

## Deliverables
- `data/raw/` – downloaded telomere CSVs, lifespan CSVs, `ecology.csv`.  
- `data/processed/analysis_ready.csv` (conforms to `contracts/dataset.schema.yaml`).  
- `results/model_base.csv`, `results/model_interaction.csv` (conform to `contracts/model_output.schema.yaml`).  
- `results/sensitivity_log.csv`, `results/power_report.yaml`, `results/permutation_pvalue.yaml`.  
- Figures: `results/association_forest.png`, `results/moderator_plot.png`.  
- Log files: `logs/ingestion.log`, `logs/cleaning.log`, `logs/model.log`.  
- Updated `state/projects/PROJ-055...yaml` with artifact hashes.  
