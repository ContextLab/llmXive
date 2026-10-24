# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-10-23 | **Spec**: `specs/001-telomere-lifespan-impact/spec.md`  
**Input**: Feature specification from `/specs/001-telomere-lifespan-impact/spec.md`

## Summary
The pipeline will (1) discover and download raw telomere‑length measurements from Dryad and lifespan/ecological covariates from the open AnAge export (fallback to BirdLife International), (2) filter to avian species via Open Tree of Life taxonomic validation, (3) standardize all telomere units to kilobases (including documented qPCR‑to‑kb conversion), (4) aggregate to species‑level means (including mean adult lifespan), (5) fetch a bird phylogeny from Open Tree of Life and fit a **phylogenetic generalized least‑squares (PGLS) model** that includes body mass as a confounder, (6) extend the PGLS with interaction terms for migration status and breeding latitude, (7) conduct a sensitivity analysis (LOOCV‑by‑species or jackknife‑by‑study) and a **simulation‑based power calculation** that mirrors the phylogenetic GLS, and (8) generate a forest plot of fixed effects and moderator visualizations. All steps are deterministic, checksum‑protected, and runnable on a GitHub Actions free‑tier runner (CPU‑only, ≤ 7 GB RAM, ≤ 6 h). No GPU is required.

## Technical Context
- **Language/Version**: Python 3.11, R 4.3 (accessed via `rpy2`)
- **Primary Dependencies**:  
  - Python: `pandas`, `numpy`, `requests`, `pyyaml`, `rpy2`, `matplotlib`, `scipy`, `tqdm`  
  - R: `nlme`, `ape`, `ggplot2`, `patchwork`, `performance`, `lmerTest`
- **Storage**: Local filesystem (`data/`, `results/`, `logs/`)
- **Testing**: `pytest`; schema validation via `jsonschema`
- **Target Platform**: Linux (GitHub Actions free runner)
- **Constraints**: Memory < 6 GB, total runtime ≤ 6 h
- **Scale/Scope**: Whole‑population meta‑analysis across ≥ 15 bird species (target), > 500 individuals total

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed seeds, deterministic scripts, SHA‑256 checksums recorded. |
| II. Verified Accuracy | PASS | Only open APIs (Dryad, AnAge/BirdLife, OpenTree) are used; no fabricated URLs. |
| III. Data Hygiene | PASS | Raw files immutable, every transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | PASS | All figures and statistics trace back to `data/processed/merged_analysis.csv` and the version‑controlled scripts that generated them. |
| V. Versioning Discipline | PASS | Artifact hashes stored in `state/projects/PROJ-055...yaml`. |
| VI. Ecological Data Integration | PASS | Covariates sourced from AnAge; BirdLife used only when AnAge lacks a field, satisfying the constitutionally mandated fallback. |
| VII. Statistical Modeling Transparency | PASS | Model formulas, fixed effects, interaction terms, and phylogenetic correlation structures are logged in script headers; all model objects saved as versioned artifacts. |

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| 0 – Discovery | `01_discover_data.py` queries Dryad, writes discovered DOIs to `config.yaml`. aborts with `Data Availability Error` if none found. | FR‑001 | — |
| 1 – Ingestion | `02_ingest_data.py` downloads each DOI, stores raw copies under `data/raw/`, computes SHA‑256 checksums. | FR‑001 | SC‑001 |
| 2 – Cleaning & Standardization | `03_clean_merge.py` (a) **Taxonomic filter**: retain only taxa resolved as birds via OpenTree; (b) **Unit conversion**: apply documented qPCR‑to‑kb factors (cited in research.md); (c) filter to wild‑caught juveniles; (d) merge telomere and covariate tables on species (case‑insensitive). Writes `missing_data_log.csv`, `unconvertible_units.csv`, `unit_conversion_log.csv`, and `data/processed/merged_analysis.csv`. | FR‑002, FR‑003 | SC‑001 |
| 3 – Modeling (Base PGLS) | `04_fit_pgls_base.py` fits `mean_lifespan_days ~ telomere_length_kb + body_mass_g + (1|species)` via `nlme::gls` with `corPagel` correlation matrix derived from the fetched phylogeny. If `n_species < 15`, writes low‑power flag and null statistics. | FR‑004 (now includes body mass) | SC‑002 |
| 4 – Modeling (Interaction PGLS) | `05_fit_pgls_interaction.py` fits `mean_lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + body_mass_g + (1|species)` using the same phylogenetic correlation. Rows with `migration_status == "Unknown"` are excluded from interaction estimation and logged. | FR‑005, FR‑008 | SC‑003 |
| 5 – Sensitivity & Power | `06_sensitivity_power.py` runs LOOCV‑by‑species when `n_species ≥ 10`; otherwise jackknife‑by‑study. Simulates 1 000 phylogenetic datasets using the observed tree and Pagel’s λ, injecting a standardized telomere slope of 0.2 (partial‑R² ≈ 0.04). Fits the **same PGLS** to each simulated dataset; power = proportion with `p < 0.05`. Logs method choice. | FR‑006 | SC‑004, SC‑005 |
| 6 – Visualization | `07_visualize.py` creates `association_forest.png` (fixed‑effect forest plot) and `moderator_plot.png` (grouped scatter for migration status and latitude gradient). | FR‑007 | — |

## Compute Feasibility
All Python and R code runs comfortably on 2 vCPU / 7 GB RAM; total wall‑clock time is on the order of tens of minutes on the free tier. No GPU components are required.

## Risk Mitigation
- **Missing external data** → hard failure (`Data Availability Error`). No synthetic substitution.
- **Memory overrun** → chunked CSV processing (`chunksize=100_000`).
- **Model non‑convergence** → retry with alternative optimizer settings; if still failing, report null statistics with diagnostic log.
- **Low species count** → low‑power flag per FR‑004; downstream steps still run (power simulation, visualizations) but statistical fields are null.

## Deliverables
- `data/processed/merged_analysis.csv` (validated against `contracts/dataset.schema.yaml`).
- `results/model_summary.csv` (validated against `contracts/model_output.schema.yaml`).
- `results/sensitivity_log.csv`, `results/power_report.yaml`.
- `results/association_forest.png`, `results/moderator_plot.png`.
- Log files: `missing_data_log.csv`, `unconvertible_units.csv`, `unit_conversion_log.csv`, `interaction_exclusion_log.csv`.
- `state/projects/PROJ-055...yaml` updated with artifact hashes and run summary.

---

