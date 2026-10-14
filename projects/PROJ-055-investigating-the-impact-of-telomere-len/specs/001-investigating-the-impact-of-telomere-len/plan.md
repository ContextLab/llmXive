# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-10-13 (revised) | **Spec**: `specs/001-telomere-len-impact/spec.md`
**Input**: Feature specification from `/specs/001-telomere-len-impact/spec.md`

## Summary
The pipeline will (1) discover and download raw telomere‑length data via the Dryad public REST API and lifespan/ecological covariates from AnAge (or BirdLife International as a fallback), (2) standardize units to kilobases, filter to wild‑caught early‑life measurements, and merge on species while populating all required schema fields, (3) fetch a bird phylogeny from the Open Tree of Life, (4) fit Phylogenetic Generalized Least Squares (PGLS) models (base and interaction) with appropriate species‑count thresholds, (5) run a study‑level jackknife (or LOOCV‑by‑species when appropriate) and compute a **simulation‑based power estimate** that uses a **standardized regression slope** (partial‑R² equivalent) of 0.5 SD for telomere length, (6) generate forest‑ and moderator‑plots, and (7) record all provenance, checksums, and logs. All steps are deterministic, checksum‑protected, and runnable on a GitHub Actions free‑tier runner (CPU‑only, ≤ 7 GB RAM, ≤ 6 h).

## REAL‑DATA POLICY (resolves fabricated‑result signal)
- No synthetic, placeholder, or randomly generated numbers are written to `data/processed/` or `results/`. When the low‑power condition (n_species < 15) is met, the pipeline writes the message `"Low Power: Phylogenetic inference unreliable"`, sets `low_power_flag: true`, and **all statistical fields are set to `null`** (explicit absence of a result, not a fabricated value). No dummy coefficients are ever generated.

## Data‑Availability Scope Statement (dataset‑variable fit)
- **Dryad**: IDs are discovered at runtime by `01_discover_data.py`. If no usable datasets are found, the pipeline aborts with a `Data Availability Error`.
- **AnAge**: Primary source for lifespan, body mass, and migration status. If the AnAge export is unreachable or lacks required fields, the pipeline attempts a fallback to **BirdLife International** public records (migration status, body mass). If both sources fail, the run halts with a `Data Availability Error`.
- **Open Tree of Life**: Provides the phylogenetic tree via the `rotl` R package.
- **Human TRF reference tables** (HuggingFace URLs) are **not** used as they lack bird‑specific variables.

## Construct‑Validity Mitigation
- Filter to wild‑caught juveniles only before aggregation.
- Outlier diagnostics on species means (MAD‑based trimming) with excluded species logged.
- LOOCV‑by‑species **or** study‑level jackknife (whichever is appropriate; see Phase 6) to guard against any single study driving the telomere coefficient.
- Results are strictly associational; no causal claims are made.

## Technical Context
- **Language/Version**: Python 3.11; R 4.3 via `rpy2`.
- **Primary Dependencies**: Python: `pandas`, `numpy`, `requests`, `pyyaml`, `rpy2`, `matplotlib`, `scipy`. R: `phylolm`, `ape`, `rotl`, `pwr`.
- **Storage**: Local filesystem (`data/`, `results/`, `logs/`).
- **Testing**: `pytest`; schema validation via `jsonschema`.
- **Target Platform**: Linux (GitHub Actions free runner), CPU‑only.
- **Constraints**: memory < 6 GB; runtime ≤ 6 h.

## Constitution Check
| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Deterministic pipeline; seeds pinned; SHA‑256 hashes recorded. |
| II. Verified Accuracy | PASS | Only open APIs (Dryad, OpenTree) and BirdLife fallback are used; no fabricated URLs. |
| III. Data Hygiene | PASS | Raw files checksummed; every transformation writes a new file with documented derivation. |
| IV. Single Source of Truth | PASS | All figures/statistics trace to `data/processed/merged_analysis.csv` and versioned scripts. |
| V. Versioning Discipline | PASS | SHA‑256 hashes recorded per artifact; state YAML updated. |
| VI. Ecological Data Integration | CONDITIONAL | Primary source AnAge; BirdLife International used as constitutionally sanctioned fallback (see Phase 0). |
| VII. Statistical Modeling Transparency | PASS | Model formulas, fixed and interaction terms recorded in script headers; λ‑estimation diagnostics saved. |

## Mapping of FR & SC to Plan Phases
| Phase | Tasks | FR addressed | SC addressed |
|-------|-------|--------------|--------------|
| 0 – Data Discovery | `01_discover_data.py` queries Dryad, attempts AnAge, falls back to BirdLife if needed; aborts with `Data Availability Error` on total failure. | FR‑001 | — |
| 1 – Ingestion | `02_ingest_data.py` downloads discovered Dryad files and AnAge/BirdLife exports; records SHA‑256 checksums. | FR‑001 | SC‑001 |
| 2 – Cleaning & Standardization | `03_clean_merge.py` converts units to kb, filters wild‑caught juveniles, merges on species, writes `logs/missing_data_log.csv`, `logs/unconvertible_units.csv`, and `data/processed/merged_analysis.csv`. | FR‑002, FR‑003 | SC‑001 |
| 3 – Phylogeny Fetch | `04_fetch_phylogeny.py` uses OpenTree (`rotl`) to build induced subtree for the exact species list; logs unmatched tips. | (supports FR‑004) | — |
| 4 – Modeling (Base) | `05_fit_pgls_base.py` fits `lifespan ~ telomere_length + body_mass + measurement_method` via `phylolm` (λ model). **If n_species < 15**: writes low‑power message, sets `low_power_flag: true`, and leaves all coefficient/p‑value/λ/AIC fields **null**. | FR‑004 | SC‑002 |
| 5 – Modeling (Interaction) | `06_fit_pgls_interaction.py` fits `lifespan ~ telomere_length * migration_status + body_mass + measurement_method` **only when n_species ≥ 30**. Rows with `migration_status == "Unknown"` are **excluded** from this model (logged in `logs/interaction_exclusion_log.csv`). Reports interaction coefficient, SE, CI, p‑value, ΔAIC, and λ diagnostics. | FR‑005 | SC‑003 |
| 6 – Sensitivity & Power | `07_sensitivity.py` runs **study‑level jackknife** whenever any Dryad study contributes >1 species; otherwise LOOCV‑by‑species. Logs justification. **Power simulation**: generates 1,000 phylogenetic datasets using the observed tree and estimated λ, injecting a **standardized regression slope of 0.5 SD** for telomere length (equivalent to a partial‑R² of 0.25). Fits the base PGLS on each simulated dataset and records the proportion with `p_telomere < α`. Reports this proportion as `power_estimate` in `results/power_report.yaml`. | FR‑006 | SC‑004, SC‑005 |
| 7 – Visualization | `08_visualize.py` generates `results/association_forest.png` (uses `fixed_effect`, `se_telomere`, `ci_lower`, `ci_upper`) and `results/moderator_plot.png` (grouped scatter with regression lines for Migratory vs Resident). | FR‑007 | — |

## Compute Feasibility
- **CPU‑first**: All Python/R operations run comfortably within < 2 GB RAM; total runtime minutes. No GPU components needed.

## Risk Mitigation
- **Missing external data** → hard failure with `Data Availability Error`; scope revision required, never synthetic substitution.
- **Memory overrun** → chunked CSV processing (`chunksize`).
- **Model convergence failure** → retry with fixed λ = 0 and λ = 1; if still failing, report null statistics with diagnostics.
- **R packages** → installed by `code/R/install_packages.R` on first run; no renv dependency (renv verification disabled).

## Deliverables
- `data/processed/merged_analysis.csv` (FR‑001–FR‑003), validated against `contracts/dataset.schema.yaml`.
- `results/model_summary.csv` (FR‑004, FR‑005), validated against `contracts/model_output.schema.yaml`; null statistical fields with `low_power_flag: true` when n_species < 15.
- `results/sensitivity_log.csv` (FR‑006) – log‑only artifact (no schema).
- `results/power_report.yaml` (SC‑005).
- `results/association_forest.png`, `results/moderator_plot.png` (FR‑007).
- `logs/missing_data_log.csv`, `logs/unconvertible_units.csv`, `logs/unit_conversion_log.csv`, `logs/interaction_exclusion_log.csv`.
- State YAML with artifact hashes and a `run_summary` recording data‑provenance status (real‑data success or hard failure — never “synthetic”).
