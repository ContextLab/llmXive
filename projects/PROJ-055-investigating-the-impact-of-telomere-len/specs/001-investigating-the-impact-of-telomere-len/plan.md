# Implementation Plan: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

**Branch**: `001-telomere-lifespan-impact` | **Date**: 2026-10-24 | **Spec**: `specs/001-telomere-lifespan-impact/spec.md`  
**Input**: Feature specification from `/specs/001-telomere-lifespan-impact/spec.md`

## Summary
The pipeline downloads open‑access telomere‑length CSVs from Dryad and individual‑level lifespan CSVs from verified open bird‑lifespan repositories, merges them with ecological covariates sourced from AnAge and BirdLife International, and performs a Linear Mixed‑Effects Model (LMM) analysis with interaction terms. An external permutation test and a random‑effects meta‑analysis provide non‑circular significance benchmarks and heterogeneity assessment. All steps are deterministic, checksum‑verified, and run on the CPU‑only GitHub Actions free tier.

## Technical Context

**Language/Version**: Python 3.11, R 4.3 (accessed via `rpy2`)  
**Primary Dependencies**  
- Python: `pandas`, `numpy`, `requests`, `pyyaml`, `rpy2`, `matplotlib`, `tqdm`, `jsonschema`  
- R: `lme4`, `lmerTest`, `metafor`, `ggplot2`, `patchwork`  
**Storage**: Local filesystem (`data/`, `results/`, `logs/`)  
**Testing**: `pytest` + JSON‑Schema validation (`jsonschema`)  
**Target Platform**: Linux (GitHub Actions free tier)  
**Constraints**: ≤ 7 GB RAM, ≤ 6 h wall‑clock, CPU‑only (no GPU needed)  
**Scale/Scope**: Real open datasets (Dryad telomere, verified bird‑lifespan CSVs, AnAge/BirdLife covariates). All quantitative statements are deferred to the research phase.

## Global Determinism
All scripts read the `seed` value from `code/config.yaml` and set:
```python
np.random.seed(config.seed)
random.seed(config.seed)
```
and in R:
```R
set.seed(config$seed)
```
ensuring reproducibility (Constitution I).

## Phase Overview

| Phase | Script | Description | FR(s) addressed | SC(s) addressed |
|-------|--------|-------------|----------------|-----------------|
| 0 – Configuration | `code/config.yaml` | Static, **verified** URLs for Dryad telomere, verified bird‑lifespan, and AnAge/BirdLife ecological CSVs (as listed in the project’s “Verified datasets” block). | FR‑001 | — |
| 1 – Ingestion | `02_ingest_data.py` | Downloads each CSV, records SHA‑256 checksums, stores under `data/raw/`. Fails if any download fails. | FR‑001 | SC‑001 (total rows) |
| 2 – Cleaning & Merge | `03_clean_merge.py` | Renames columns, records `measurement_method` and `batch_id`, converts telomere units to kb (handling qPCR Ct → kb via documented conversion), **preserves measurement‑method heterogeneity** and batch identifiers for later modelling, adds `sex` and `age_at_measurement_days`, filters wild‑caught individuals, merges telomere, lifespan, and ecological covariates on `species_id`. Writes `data/processed/analysis_ready.csv`, `missing_data_log.csv`, `unconvertible_units.csv`. **Validates** `analysis_ready.csv` against `contracts/dataset.schema.yaml`. | FR‑002, FR‑003, FR‑005, FR‑008, FR‑011 | SC‑001 (proportion merged) |
| 3 – Dataset Size Verification | `04_verify_dataset_size.py` | Checks that `analysis_ready.csv` contains **≥ 500 rows** and **≥ 10 distinct species**; aborts with a clear error if not (fulfills FR‑011). | FR‑011 | SC‑001 (size check) |
| 4 – Ecological Covariates | `04_fetch_ecology.py` | Retrieves migration status, breeding latitude, and body mass from **verified AnAge/BirdLife CSVs** (open). Stores as `data/raw/ecology.csv` with provenance fields. | FR‑002, FR‑003, VI | — |
| 5 – R Packages Verification | `04_verify_r_packages.py` | Ensures required R packages (`lme4`, `lmerTest`, `metafor`) are installed; installs missing ones via `install.packages`. | — | — |
| 6 – Modelling (Base LMM) | `05_fit_lmm_base.py` | Fits `lifespan_days ~ telomere_length_kb + sex + age_at_measurement_days + body_mass_g + breeding_latitude + (1|species_id) + (1|batch_id)` via `lme4::lmer`. Includes **sex, age, body mass, breeding latitude, and batch** as covariates/random effects. Logs low‑power warning if `n_species < 15`. | FR‑004, FR‑005, FR‑008 | SC‑002 (α = 0.05), SC‑005 (conditional) |
| 7 – Modelling (Interaction LMM) | `06_fit_lmm_interaction.py` | Fits `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + sex + age_at_measurement_days + body_mass_g + (1|species_id) + (1|batch_id)`. Rows with `migration_status == "Unknown"` are **included as a distinct category**; interaction terms are estimated for the three categories. | FR‑005, FR‑008 | SC‑003 (ΔAIC) |
| 8 – Sensitivity & Power | `07_sensitivity_power.py` | **Sensitivity**: LOOCV‑by‑species when `n_species ≥ 10`; otherwise jackknife‑by‑data‑source. Each iteration refits the base LMM; coefficient stability recorded in `results/sensitivity_log.csv`. **Power**: Runs **only when `n_species ≥ 15`**. Simulates a substantial number of datasets per effect size (0.05–0.30) using observed variance components; records power curves in `results/power_report.yaml`. | FR‑006, SC‑004, SC‑005 | — |
| 9 – Random‑Effects Meta‑Analysis | `09_meta_analysis.py` | **Per‑species slopes**: Fits an LMM for each species (same covariates as the base model) to obtain species‑specific telomere coefficients. **Meta‑analysis**: Aggregates these slopes with `metafor::rma` (random‑effects). Produces the I² heterogeneity statistic, an overall effect estimate, and a forest plot `results/meta_forest.png`. Validates output against `contracts/meta_analysis.schema.yaml`. | FR‑009 | SC‑006 (I²) |
|10 – External Significance Validation | `08_permutation_test.py` | Generates a large number of permutations of `lifespan_days`, refits the base LMM each time, and computes an empirical p‑value for the telomere coefficient. Saves `results/permutation_pvalue.yaml`. **Dual‑p‑value Significance Flag**: true only when both model‑based p‑value and permutation p‑value < 0.05. | — | SC‑002 (empirical benchmark) |
|11 – Visualisation | `09_visualise.py` | Generates `results/association_forest.png` (fixed‑effect forest plot), `results/moderator_plot.png` (grouped scatter for migration status and latitude gradient), and `results/meta_forest.png` (species‑level meta‑analysis forest plot). | FR‑007 | — |
|12 – Validation & Reporting | `10_validate_report.py` | Validates `analysis_ready.csv` against `contracts/dataset.schema.yaml`, validates model outputs against `contracts/model_output.schema.yaml`, validates meta‑analysis output against `contracts/meta_analysis.schema.yaml`, and assembles `results/report.yaml` summarising all SCs, including the dual‑p‑value significance flag. | — | All SCs |

## Compute Feasibility
All steps run comfortably on 2 vCPU / 7 GB RAM; total wall‑clock < 30 minutes. No GPU escape hatch is needed.

## Risk Mitigation
- **Missing authentic data** – URLs are static and verified; ingestion aborts with a clear “Data Unavailable” error if any download fails. No placeholder data are used.  
- **Memory overrun** – CSVs are streamed (`chunksize=50_000`).  
- **Model non‑convergence** – Switches to `bobyqa` optimizer; if still failing, writes low‑power flag and exits gracefully.  
- **Low‑species count** – Emits low‑power warning and skips power simulation, but still runs meta‑analysis (which can handle few species).  
- **Circular significance** – Permutation test supplies an external benchmark for SC‑002, breaking circularity.  
- **R‑package verification** – Python‑driven verifier guarantees required R packages are present.  
- **Determinism** – All scripts set `numpy.random.seed(config.seed)` and `set.seed(config.seed)` (see Constitution Check).  

## Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I. Reproducibility | PASS | Fixed random seeds set in every script, SHA‑256 checksums recorded for every file. |
| II. Verified Accuracy | PASS | All external data fetched from verified URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | PASS | Raw files immutable; each transformation writes a new file with provenance metadata. |
| IV. Single Source of Truth | PASS | All figures and statistics trace back to `data/processed/analysis_ready.csv` and version‑controlled scripts. |
| V. Versioning Discipline | PASS | Artifact hashes stored in `state/projects/PROJ-055...yaml`. |
| VI. Ecological Data Integration | PASS | Covariates sourced from AnAge and BirdLife International public records, with provenance fields. |
| VII. Statistical Modeling Transparency | PASS | LMM and meta‑analysis scripts under `code/`, formulas explicit in headers, outputs saved as versioned artifacts. |

## Deliverables
- `data/raw/` – downloaded telomere CSVs, lifespan CSVs, and ecological covariate files.  
- `data/processed/analysis_ready.csv` (conforms to `contracts/dataset.schema.yaml`).  
- `results/model_base.csv` and `results/model_interaction.csv` (conform to `contracts/model_output.schema.yaml`).  
- `results/meta_analysis.yaml` and `results/meta_forest.png` (conform to `contracts/meta_analysis.schema.yaml`).  
- `results/sensitivity_log.csv`, `results/power_report.yaml`, `results/permutation_pvalue.yaml`.  
- Figures: `results/association_forest.png`, `results/moderator_plot.png`, `results/meta_forest.png`.  
- Log files: `logs/ingestion.log`, `logs/cleaning.log`, `logs/model.log`.  
- Updated `state/projects/PROJ-055...yaml` with artifact hashes. ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-055-investigating-the-impact-of-telomere-len/specs/001-investigating-the-impact-of-telomere-len/research.md===
# Research: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Executive Summary
The pipeline now **requires** authentic telomere‑length data from Dryad and individual‑level lifespan records from **verified open bird‑lifespan repositories** (e.g., AnAge‑derived or BirdLife datasets). Ecological covariates are fetched from **AnAge and BirdLife International** (verified open sources). If any required variable is absent, the run aborts with a clear error, guaranteeing construct validity. When all inputs are present, the full analytical workflow (download → cleaning → merging → LMM → interaction analysis → sensitivity & power → meta‑analysis → permutation validation → visualisation) is executed reproducibly and transparently, with all results explicitly labeled as **associational**.

## Real‑Data Policy
- No synthetic rows are fabricated.  
- The configuration step validates that each required variable (**telomere_length_kb**, **lifespan_days**, **species_id**, **migration_status**, **breeding_latitude**, **body_mass_g**, **sex**, **age_at_measurement_days**, **measurement_method**, **batch_id**) exists in the raw downloads **before** any analysis.  
- If a required column is missing, the pipeline aborts with a `Data Mismatch Error` and logs the missing fields; no downstream modelling is performed.  
- All statistical conclusions are labeled **associational**; no causal language is used.

## Dataset Strategy

| Needed Variable | Source (Verified) | Access Method | Fit Check |
|-----------------|-------------------|---------------|-----------|
| Telomere length (kb) | Dryad dataset(s) containing avian telomere measurements (e.g., DOI ) | `requests` download via static URLs in `config.yaml` (must be the verified URLs listed in the project’s “Verified datasets” block) | Verified presence after download |
| Lifespan (days) | Verified open bird‑lifespan repository (e.g., BirdLife Lifespan dataset) | Direct HTTP download (static URLs in `config.yaml`; **must be verified URLs from the “Verified datasets” block**) | Verified presence after download |
| Species identifier | Column `species` in telomere or lifespan files (standardised) | Merged during cleaning | Verified presence |
| Migration status | AnAge/BirdLife International CSV (open) | Direct CSV download (static URLs in `config.yaml`; verified) | Verified presence |
| Breeding latitude | AnAge/BirdLife International CSV (open) | Direct CSV download (static URLs in `config.yaml`; verified) | Verified presence |
| Body mass (g) | AnAge/BirdLife International CSV (open) | Direct CSV download (static URLs in `config.yaml`; verified) | Verified presence |
| Sex | Same as above (included in source CSVs) | — | Verified presence |
| Age at measurement (days) | Same as above | — | Verified presence |
| Measurement method | Metadata column in Dryad telomere files | — | Verified presence |
| Batch ID | Metadata column in Dryad telomere files | — | Verified presence |

*All sources are open, programmatically accessible, and listed in the verified datasets block. The ingestion script aborts if any required column is absent, guaranteeing that the analysis never proceeds with incomplete variables.*

### Dataset‑Variable Fit Check (fatal if wrong)
The ingestion script validates that each required column exists **after** renaming and unit conversion. If any column is missing, the pipeline raises a `Data Mismatch Error` and stops. This prevents any tautological “fit” based solely on placeholder renaming.

## Integration Plan
1. **Configuration** (`code/config.yaml`): static, **verified** URLs for Dryad telomere CSVs, verified bird‑lifespan CSVs, and AnAge/BirdLife ecological CSVs (as listed in the “Verified datasets” block). |
2. **Ingestion** (`02_ingest_data.py`): downloads each file, records SHA‑256 checksums, stores under `data/raw/`. |
3. **Cleaning & Merge** (`03_clean_merge.py`): renames columns, records `measurement_method` and `batch_id`, converts telomere units to kb (handling qPCR Ct → kb), adds `sex` and `age_at_measurement_days`, filters wild‑caught individuals, merges telomere, lifespan, and ecological tables on `species_id`. Generates `analysis_ready.csv`, `missing_data_log.csv`, `unconvertible_units.csv`. **Validates** `analysis_ready.csv` against `contracts/dataset.schema.yaml`. |
4. **Dataset Size Verification** (`04_verify_dataset_size.py`): ensures ≥ 500 rows and ≥ 10 species; aborts otherwise (fulfills FR‑011). |
5. **Ecology Fetch** (`04_fetch_ecology.py`): pulls migration status, breeding latitude, and body mass from verified AnAge/BirdLife CSVs, stores as `data/raw/ecology.csv` with provenance fields. |
6. **R Packages Verification** (`04_verify_r_packages.py`): ensures required R packages (`lme4`, `lmerTest`, `metafor`) are installed before any R‑based modelling. |
7. **Base LMM** (`05_fit_lmm_base.py`): fits `lifespan_days ~ telomere_length_kb + sex + age_at_measurement_days + body_mass_g + breeding_latitude + (1|species_id) + (1|batch_id)`. Logs low‑power warning if `n_species < 15`. |
8. **Interaction LMM** (`06_fit_lmm_interaction.py`): fits `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + sex + age_at_measurement_days + body_mass_g + (1|species_id) + (1|batch_id)`. Rows with `migration_status == "Unknown"` are **included as a distinct category**; interaction terms are estimated for the three categories. |
9. **Sensitivity & Power** (`07_sensitivity_power.py`):  
   - **Sensitivity**: Performs LOOCV‑by‑species when `n_species ≥ 10`; otherwise jackknife‑by‑data‑source.  
   - **Power**: Runs **only when `n_species ≥ 15`**. Simulates a substantial number of datasets across telomere effect sizes 0.05–0.30; records power curves in `results/power_report.yaml`. |
10. **Random‑Effects Meta‑Analysis** (`09_meta_analysis.py`): fits per‑species LMMs to obtain species‑specific telomere‑lifespan slopes, aggregates them via `metafor::rma` (random‑effects), outputs the I² heterogeneity statistic and a forest plot `results/meta_forest.png`. Validates output against `contracts/meta_analysis.schema.yaml`. |
11. **External Significance Validation** (`08_permutation_test.py`): Generates a substantial number of label‑permuted versions of `analysis_ready.csv`, refits the base LMM each time, and computes an empirical p‑value for the telomere coefficient. Saves `results/permutation_pvalue.yaml`. Significance declared only when **both** the model‑based p‑value and the permutation‑derived p‑value are `< 0.05`. |
12. **Visualisation** (`09_visualise.py`): Generates `results/association_forest.png` (fixed‑effect forest plot), `results/moderator_plot.png` (grouped scatter for migration status and latitude gradient), and `results/meta_forest.png` (species‑level meta‑analysis forest plot). |
13. **Validation & Reporting** (`10_validate_report.py`): Validates `analysis_ready.csv` against `contracts/dataset.schema.yaml`, validates model outputs against `contracts/model_output.schema.yaml`, validates meta‑analysis output against `contracts/meta_analysis.schema.yaml`, and assembles `results/report.yaml` summarising all SCs, including the dual‑p‑value significance flag.

All scripts are version‑controlled under `code/`, read a single `config.yaml`, and contain no hidden side‑effects.

## Statistical Methodology

### Primary Model (Base LMM) – FR‑004
- **Formula**: `lifespan_days ~ telomere_length_kb + sex + age_at_measurement_days + body_mass_g + breeding_latitude + (1|species_id) + (1|batch_id)`  
- **Estimator**: REML via `lme4::lmer`.  
- **Low‑Power Handling**: If `n_species < 15`, the script writes `"Low Power: species‑level inference unreliable"` to `results/model_base.csv`, sets `low_power_flag: true`, and **does not** run the power simulation.

### Interaction Model – FR‑005 & FR‑008
- **Formula**: `lifespan_days ~ telomere_length_kb * migration_status + telomere_length_kb * breeding_latitude + sex + age_at_measurement_days + body_mass_g + (1|species_id) + (1|batch_id)`  
- **Exclusions**: Rows where `migration_status == "Unknown"` are **included as a distinct category**; interaction terms are estimated for the three categories.  

### Meta‑Analysis – FR‑009
- **Per‑Species Slopes**: Fit an LMM for each species (same covariates as the base model) to obtain species‑specific telomere coefficients.  
- **Random‑Effects Aggregation**: Use `metafor::rma` to combine slopes, yielding an overall effect, 95 % CI, and **I² heterogeneity statistic**.  
- **Outputs**: Species‑level table (`results/meta_analysis.yaml`) and forest plot (`results/meta_forest.png`).  

### Sensitivity – FR‑006, SC‑004
- **LOOCV‑by‑species** if `n_species ≥ 10`; otherwise **jackknife‑by‑data‑source**. Each iteration refits the base LMM; coefficient stability recorded in `results/sensitivity_log.csv`.

### Power – SC‑005 (Revised)
- **Simulation‑based, range‑of‑effects**: 1 000 synthetic datasets are generated for each telomere effect size in the grid {0.05, 0.10, 0.15, 0.20, 0.25, 0.30}. Variance components are taken from the observed data. Power for each effect size is the proportion of simulations with `p_telomere < 0.05`.  
- **Runs only when `n_species ≥ 15`; otherwise a note “Power analysis not performed due to insufficient species” is written.**

### External Significance Validation – SC‑002 (Addressed)
- **Permutation Test**: 10 000 permutations of the response variable (`lifespan_days`) break any true association while preserving covariate structure. The empirical p‑value is the proportion of permuted coefficients as extreme as the observed telomere coefficient.  
- **Dual‑p‑value Significance Flag**: `significance_flag` is set to `true` only if **both** the model‑based p‑value and the permutation‑derived p‑value are `< 0.05`. This external benchmark eliminates circular reliance on the model’s own p‑value.

### Multiple Comparisons & Alpha – SC‑002
- Primary hypothesis uses α = 0.05 (set in `config.yaml`). No correction needed because only one primary fixed effect is pre‑specified; interaction terms are exploratory and reported without correction.

### Causal Framing
- All statements are explicitly **associational**; no causal language is used.

## Compute Feasibility (CPU‑first)
All steps run comfortably on 2 vCPU / 7 GB RAM; total wall‑clock < 30 minutes. No GPU escape hatch is needed.

## Decision/Rationale
- **CPU‑first**: All libraries (`pandas`, `lme4`, `metafor`) have pure‑CPU implementations.  
- **Verified data only**: The pipeline fetches data exclusively from **open, verified URLs** listed in the verified datasets block.  
- **Modular scripts**: Each phase writes explicit logs and checksum files, enabling deterministic verification.  
- **External validation**: The permutation test satisfies the methodological panel’s demand for a non‑circular significance assessment.  
- **Future‑proof**: Adding new datasets only requires updating the static URL list; the rest of the pipeline remains unchanged.

## Quick Reference of Scripts (existence confirmed)
- `code/config.yaml` (static URLs)  
- `code/02_ingest_data.py`  
- `code/03_clean_merge.py`  
- `code/04_fetch_ecology.py`  
- `code/04_verify_r_packages.py`  
- `code/04_verify_dataset_size.py`  
- `code/05_fit_lmm_base.py`  
- `code/06_fit_lmm_interaction.py`  
- `code/07_sensitivity_power.py`  
- `code/08_permutation_test.py`  
- `code/09_meta_analysis.py`  
- `code/09_visualise.py`  
- `code/10_validate_report.py`

All scripts are deterministic, read `code/config.yaml`, and contain no hidden side‑effects.

---



## projects/PROJ-055-investigating-the-impact-of-telomere-len/specs/001-investigating-the-impact-of-telomere-len/data-model.md===
# Data Model: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Overview
Four artifact classes are produced:

1. **Raw ingestion files** – immutable copies of the downloaded Dryad telomere CSVs, lifespan CSVs, and ecological covariate files from verified AnAge/BirdLife sources.  
2. **Processed analysis dataset** – `data/processed/analysis_ready.csv` conforming to `contracts/dataset.schema.yaml`. This file is generated by `03_clean_merge.py`, which now **explicitly creates** the provenance columns required by the schema (`n_obs`, `source_file`, `checksum`), and additionally records `measurement_method`, `batch_id`, `sex`, and `age_at_measurement_days` to capture heterogeneity and confounding.  
3. **Model output artifacts** – `results/model_base.csv` and `results/model_interaction.csv` conforming to `contracts/model_output.schema.yaml`.  
4. **Meta‑analysis output** – `results/meta_analysis.yaml` and `results/meta_forest.png` conforming to `contracts/meta_analysis.schema.yaml`, containing species‑specific slopes and the I² heterogeneity statistic.

All artifacts are version‑hashed; no synthetic records are introduced.

## Entity Definitions

### SpeciesRecord (analysis dataset)
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `species_id` | string | Canonical species identifier (renamed from source). | Unique, non‑empty |
| `telomere_length_kb` | number | Telomere length in kilobases. | > 0 |
| `lifespan_days` | number | Lifespan in days. | > 0 |
| `migration_status` | string | Migration status of the species proxy. | Enum |
| `breeding_latitude` | number | Mean breeding latitude (decimal degrees). | -90 ≤ value ≤ 90 |
| `body_mass_g` | number | Body mass in grams. | > 0 |
| `sex` | string | Sex of the individual. | Enum |
| `age_at_measurement_days` | number | Age of the individual at telomere measurement (days). | ≥ 0 |
| `measurement_method` | string | Method used to obtain telomere length. | enum: "qPCR", "TRF", "Other" |
| `batch_id` | string | Identifier for the laboratory batch or study source. |
| `n_obs` | integer | Number of raw rows aggregated into this species proxy. | ≥ 1 |
| `source_file` | string | Path to the raw CSV file(s) that contributed to this record. |
| `checksum` | string | SHA‑256 checksum of the raw row block used to create this record. |
required:
  - species_id
  - telomere_length_kb
  - lifespan_days
  - migration_status
  - breeding_latitude
  - body_mass_g
  - sex
  - age_at_measurement_days
  - measurement_method
  - batch_id
  - n_obs
  - source_file
  - checksum
additionalProperties: false

### ModelResult
| Field | Type | Description |
|------|------|-------------|
| `model_type` | string | "LMM_Base" or "LMM_Interaction" |
| `fixed_effect_telomere` | number \| null | Coefficient for telomere length. |
| `se_telomere` | number \| null | Standard error for telomere coefficient. |
| `ci_lower_telomere` | number \| null | 95 % CI lower bound for telomere coefficient. |
| `ci_upper_telomere` | number \| null | 95 % CI upper bound for telomere coefficient. |
| `fixed_effect_body_mass` | number \| null | Coefficient for body mass. |
| `se_body_mass` | number \| null | Standard error for body mass. |
| `ci_lower_body_mass` | number \| null | 95 % CI lower bound for body mass. |
| `ci_upper_body_mass` | number \| null | 95 % CI upper bound for body mass. |
| `fixed_effect_migration` | number \| null | Coefficient for migration status (interaction model only). |
| `se_migration` | number \| null | Standard error for migration coefficient. |
| `ci_lower_migration` | number \| null | 95 % CI lower bound for migration coefficient. |
| `ci_upper_migration` | number \| null | 95 % CI upper bound for migration coefficient. |
| `interaction_effect_migration` | number \| null | Telomere × migration interaction coefficient. |
| `se_interaction_migration` | number \| null | Standard error for interaction coefficient. |
| `ci_lower_interaction_migration` | number \| null | 95 % CI lower bound for interaction coefficient. |
| `ci_upper_interaction_migration` | number \| null | 95 % CI upper bound for interaction coefficient. |
| `interaction_effect_latitude` | number \| null | Telomere × latitude interaction coefficient. |
| `se_interaction_latitude` | number \| null | Standard error for latitude interaction coefficient. |
| `ci_lower_interaction_latitude` | number \| null | 95 % CI lower bound for interaction coefficient. |
| `ci_upper_interaction_latitude` | number \| null | 95 % CI upper bound for interaction coefficient. |
| `p_value_telomere` | number \| null | Two‑sided p‑value for telomere coefficient. |
| `p_value_interaction_migration` | number \| null | p‑value for telomere × migration interaction. |
| `p_value_interaction_latitude` | number \| null | p‑value for telomere × latitude interaction. |
| `significance_flag` | boolean | True when both model‑based and permutation p‑values are < 0.05. |
| `aic_score` | number \| null | Akaike Information Criterion. |
| `delta_aic` | number \| null | ΔAIC vs. base model (only for interaction model). |
| `n_species` | integer | Number of unique `species_id` used in the fit. |
| `low_power_flag` | boolean | True when species count < 15. |
| `low_power_message` | string \| null | Message explaining low‑power condition. |
| `power_estimate` | number \| null | Simulated power to detect a standardized slope of 0.2 at α = 0.05. |
| `permutation_pvalue` | number \| null | Empirical p‑value from permutation test (Phase 8). |
required:
  - model_type
  - fixed_effect_telomere
  - se_telomere
  - ci_lower_telomere
  - ci_upper_telomere
  - fixed_effect_body_mass
  - se_body_mass
  - ci_lower_body_mass
  - ci_upper_body_mass
  - p_value_telomere
  - significance_flag
  - n_species
  - low_power_flag
additionalProperties: false

### MetaAnalysisResult (new)
| Field | Type | Description |
|-------|------|-------------|
| `species_id` | string | Species identifier. |
| `slope_telomere` | number | Species‑specific telomere‑lifespan slope. |
| `se_slope` | number | Standard error of the slope. |
| `ci_lower_slope` | number | 95 % confidence interval lower bound for the slope. |
| `ci_upper_slope` | number | 95 % confidence interval upper bound for the slope. |
| `i2` | number | I² heterogeneity statistic for the overall random‑effects meta‑analysis. |
required:
  - species_id
  - slope_telomere
  - se_slope
  - ci_lower_slope
  - ci_upper_slope
  - i2
additionalProperties: false

## Data Flow
1. `01_discover_data.py` → `config.yaml.dataset_urls` & `config.yaml.lifespan_urls`.  
2. `02_ingest_data.py` → `data/raw/` (raw CSVs) + checksum files.  
3. `03_clean_merge.py` → `data/processed/analysis_ready.csv` (validated against `contracts/dataset.schema.yaml`). Generates provenance columns and heterogeneity metadata.  
4. `04_fetch_ecology.py` → `data/raw/ecology.csv`.  
5. `04_verify_dataset_size.py` → aborts if FR‑011 not satisfied.  
6. `05_fit_lmm_base.py` → `results/model_base.csv` (validated against `contracts/model_output.schema.yaml`).  
7. `06_fit_lmm_interaction.py` → `results/model_interaction.csv` (same schema).  
8. `07_sensitivity_power.py` → `results/sensitivity_log.csv`, `results/power_report.yaml`.  
9. `09_meta_analysis.py` → `results/meta_analysis.yaml` (validated against `contracts/meta_analysis.schema.yaml`) and `results/meta_forest.png`.  
10. `08_permutation_test.py` → `results/permutation_pvalue.yaml`.  
11. `09_visualise.py` → PNGs in `results/`.  
12. `10_validate_report.py` → `results/report.yaml` (summary of all SCs).

Every step writes a checksum file and updates `state/projects/PROJ-055...yaml`, guaranteeing reproducibility (Constitution I).
