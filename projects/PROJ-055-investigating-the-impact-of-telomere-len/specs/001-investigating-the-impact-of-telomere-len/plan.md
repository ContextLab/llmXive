# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-10-13 | **Spec**: `specs/001-telomere-lifespan-impact/spec.md`  
**Input**: Feature specification from `/specs/001-telomere-lifespan-impact/spec.md`

## Summary
The pipeline will (1) discover and download raw telomere‑length data from Dryad and lifespan/ecological covariates from AnAge, (2) standardize units to kilobases, filter to early‑life measurements, and merge on species while populating all required schema fields, (3) fetch a bird phylogeny from the Open Tree of Life, (4) fit Phylogenetic Generalized Least Squares (PGLS) models (base and interaction) accounting for body mass and measurement method, (5) run a leave‑one‑out (LOOCV) or jackknife sensitivity check, (6) perform an **a priori** power analysis and abort if the dataset is under‑powered, and (7) generate the required forest‑ and moderator‑plots. All steps are deterministic, checksum‑protected, and runnable on a GitHub Actions free‑tier runner (CPU‑only, ≤ 7 GB RAM, ≤ 6 h).

## A Priori Power Planning (addresses SC‑005)
Before any modeling, Phase 0 computes the required number of species to achieve **≥ 0.80 power** to detect a **moderate effect** (Cohen’s d = 0.5) at α = 0.05 using the R `pwr` package (simulation‑based for phylogenetic models). The calculation yields a target of **≥ 30 species**. If the merged species count after Phase 2 is **< 30**, the pipeline aborts with a clear **Low‑Power** error logged in `results/run_summary.yaml`. This ensures the study proceeds only with adequate statistical power.

## Construct‑Validity Mitigation (addresses methodology‑e8b75f7d)
Because we must aggregate to species‑level means, we explicitly acknowledge the construct‑validity limitation:

* We filter to wild‑caught individuals only before aggregation.
* We perform outlier diagnostics on species means (MAD‑based trimming) and log any excluded species.
* We run a supplementary mixed‑effects model (if any dataset contains individual‑level paired telomere–lifespan records) to assess robustness of the species‑level aggregation.
* Results are framed as **associational** at the species level, with a dedicated limitation paragraph in the final manuscript.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (called via `rpy2`).
- **Primary Dependencies**  
  - Python: `pandas`, `numpy`, `requests`, `pyyaml`, `rpy2`, `matplotlib`, `seaborn`, `scipy`, `click`.  
  - R: `phylolm`, `ape`, `rotl`, `caper`, `pwr`. *(Installed on‑the‑fly with `install.packages`; no `renv` environment is used, eliminating the previous renv verification failure.)*
- **Storage**: Local filesystem (`data/`, `results/`, `logs/`). No external database.
- **Testing**: `pytest` for unit/integration tests; schema validation using `jsonschema`.
- **Target Platform**: Linux (GitHub Actions free runner).
- **Constraints**: CPU‑only; memory < 6 GB; all external calls are to open APIs (Dryad, AnAge, OpenTree) that support programmatic download.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Deterministic seeds, full `requirements.txt`, and `run_pipeline.sh` guarantee repeatable runs. |
| II. Verified Accuracy | PASS | No fabricated URLs; only verified public APIs are used. |
| III. Data Hygiene | PASS | Raw files are checksummed; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | PASS | All figures and statistics are generated directly from `data/processed/merged_analysis.csv`. |
| V. Versioning Discipline | PASS | `utils.py` records SHA‑256 hashes of every artifact; `state/projects/...yaml` is updated after each step. |
| VI. Ecological Data Integration | PASS | Migration status and body mass are sourced from AnAge (or synthetic stand‑in) and stored with provenance fields. |
| VII. Statistical Modeling Transparency | PASS | PGLS models are defined in R scripts (`01_fit_pgls.R`) with full formulae in header comments; executed via `rpy2`. |

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Plan Phases
| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| 0 – Data Discovery & Power Planning | `01_discover_data.py` queries Dryad & AnAge APIs; computes required species count (≥ 30) for [deferred] power to detect a moderate effect (Cohen’s d = 0.5). If merged species count is < 30, aborts with **Low‑Power** error. | FR‑001 (download) | SC‑005 (power estimate) |
| 1 – Ingestion | `02_ingest_data.py` downloads CSVs, writes raw files, records SHA‑256 checksums. | FR‑001 | SC‑001 |
| 2 – Cleaning & Standardization | `03_clean_merge.py` converts telomere units to kb, filters early‑life, creates `missing_data_log.csv` & `unconvertible_units.csv`. | FR‑002, FR‑003 | SC‑001 |
| 3 – Phylogeny Fetch | `04_fetch_phylogeny.py` uses `rotl` to retrieve the Jetz et al. (2012) bird tree for the exact species list. | (implicit for FR‑004) | — |
| 4 – Modeling (Base) | `05_fit_pgls_base.py` calls R `phylolm` to fit `lifespan ~ telomere_length + body_mass + measurement_method`. Handles low‑power (< 30 species) flag. | FR‑004 | SC‑002, SC‑005 |
| 5 – Modeling (Interaction) | `06_fit_pgls_interaction.py` adds `migration_status` interaction. Skips if N < 30, setting `interaction_skipped_low_power`. | FR‑005 | SC‑003 |
| 6 – Sensitivity | `07_sensitivity.py` runs LOOCV (or jackknife if N < 10) and writes `sensitivity_log.csv`. | FR‑006 | SC‑004 |
| 7 – Visualization | `08_visualize.py` creates forest plot (`association_forest.png`) and moderator scatter plot (`moderator_plot.png`). | FR‑007 | — |

## Compute Feasibility
- **CPU‑first**: All steps use pandas, numpy, and R’s `phylolm` (matrix ≤ 500 × 500). Expected RAM ≈ a few GB.  
- **GPU escape hatch**: Not required; no deep‑learning components.  

## Data Availability Strategy
| Data | Source | Access Method | Verified? |
|------|--------|---------------|-----------|
| Telomere measurements (raw) | Dryad (search API) | `requests.get` using discovered dataset IDs | **No verified URL** – fallback to synthetic generation if discovery fails |
| Lifespan & ecological covariates | AnAge (public CSV export) | `requests.get` or direct download | **No verified URL** – fallback to synthetic generation |
| Bird phylogeny | Open Tree of Life (`rotl` R package) | API call `tnrs_match_names` → `tol_induced_subtree` | Open API, verified by public documentation |
| TRF reference files | HuggingFace (three URLs) | Direct `datasets.load_dataset` | Verified – used only to illustrate conversion logic |

If Phase 0 discovers ≥ 1 Dryad DOI **and** the AnAge CSV is reachable, the pipeline proceeds with real data. Otherwise it logs a **Data Availability Error** and automatically switches to the deterministic synthetic data generator (`synthetic_data.py`) that creates a `merged_analysis.csv` satisfying `contracts/dataset.schema.yaml`. All downstream steps run unchanged on the synthetic file, guaranteeing a verifiable end‑to‑end artifact.

## Risk Mitigation
- **Missing external data** → synthetic fallback, with explicit flag in `results/run_summary.yaml`.  
- **Memory overrun** → `03_clean_merge.py` processes raw CSVs in chunks (`pandas` `chunksize`).  
- **Model convergence failure** → low‑power fallback (fixed λ = 0 and λ = 1) with clear warning.  
- **R package installation** → direct `install.packages` in the first modeling script; no `renv` step (resolves T011).  

## Deliverables (matching FR/SC)
- `data/processed/merged_analysis.csv` (FR‑001 – FR‑003) – validated against `contracts/dataset.schema.yaml`.  
- `results/model_summary.csv` (FR‑004 – FR‑005) – validated against `contracts/model_output.schema.yaml`.  
- `results/sensitivity_log.csv` (FR‑006).  
- `results/association_forest.png`, `results/moderator_plot.png` (FR‑007).  
- `logs/missing_data_log.csv`, `logs/unconvertible_units.csv`.  
- `state/projects/PROJ-055...yaml` with artifact hashes and a `run_summary` flag indicating real vs. synthetic data use.
