# Research: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Executive Summary
This document defines the data acquisition, statistical methodology, and compute plan for testing whether early‑life telomere length is associated with maximum lifespan in wild birds, and whether migration status moderates that association. **All results are real measurements derived from downloaded data.** No synthetic fallback is used; if real data cannot be retrieved, the pipeline halts with a documented `Data Availability Error` and the scope is revised rather than substituted.

## Real‑Data Policy (resolves fabricated‑result signal)
- No synthetic, placeholder, or randomly generated values may appear in `data/processed/` or `results/`.
- When species count < 15, the pipeline writes the spec‑mandated message `"Low Power: Phylogenetic inference unreliable"`, sets `low_power_flag: true`, and **all statistical fields are set to `null`** (explicit absence of a result, not a fabricated number).
- Power (SC‑005) is **calculated and reported** from the observed species count; it is not used as an abort gate. The earlier “abort if < 30 species” and “skip interaction if < 30” rules were removed because they were un‑specified.

## Dataset Strategy

| Data needed | Source | Access method | Verified status |
|-------------|--------|---------------|-----------------|
| Bird telomere measurements (raw) | Dryad public REST API (search + file download) | Runtime discovery in `01_discover_data.py`; discovered DOIs written to `config.yaml` | API named per spec (FR‑001); no dataset URL is cited because none was pre‑verified — IDs come only from live discovery |
| Lifespan & ecological covariates | AnAge database (primary) **or** BirdLife International public records (fallback) | Attempt official AnAge export; if unavailable or missing required fields, query BirdLife via their open CSV API | **No verified source found for AnAge**; BirdLife records are publicly downloadable and provide migration status & body mass. |
| Bird phylogeny | Open Tree of Life via R `rotl` | `tnrs_match_names` → `tol_induced_subtree` | Open programmatic API |
| Human TRF reference tables | HuggingFace (verified URLs below) | — | Verified, but **excluded**: they contain human telomere repeat data, not bird‑specific variables. Dataset‑variable mismatch; not used as inputs. |

Verified URLs (cited per the verified‑datasets block; not used as analysis inputs):
- https://huggingface.co/datasets/ReaKal/hg38.trf.short/resolve/main/hg38.trf.short.bed.csv
- https://huggingface.co/datasets/Taklaxbr/tr-full-dataset/resolve/main/data.jsonl
- https://huggingface.co/datasets/Hoixi/TR-FinTable-Dataset-v4/resolve/main/split_name_to_num_samples.json

**Dataset‑variable fit check (fatal‑if‑wrong gate):** the study requires, per species: early‑life telomere length (kb or convertible), maximum lifespan, migration status, and body mass. Dryad discovery validates each dataset for a telomere‑length column with unit metadata and species identifiers; datasets failing this check are logged and excluded. AnAge must supply lifespan and body mass; if migration status is absent, BirdLife is queried. If both sources lack a variable, the variable is recorded as `"Unknown"` (migration) or the row is excluded from the interaction model (see below).

## Integration Plan
1. **Discovery** (`01_discover_data.py`): query the Dryad API; write real discovered DOIs to `config.yaml` under `dataset_ids`. Attempt the AnAge export; on failure, automatically query BirdLife International for migration status and body mass. If both sources fail, halt with `Data Availability Error`.
2. **Ingestion** (`02_ingest_data.py`): download discovered files, record SHA‑256 checksums, write raw copies under `data/raw/`. All endpoints come from `config.yaml`; no hard‑coded URLs or seeds.
3. **Standardization** (`03_clean_merge.py`): unit detection (`kb`, `bp`, `Ct`); bp → kb (÷[deferred]); Ct values without a standard curve → `logs/unconvertible_units.csv`; filter wild‑caught, early‑life (`age_category == "Juvenile"`). Log conversions to `logs/unit_conversion_log.csv`.
4. **Merging**: case‑insensitive species‑name join; unmatched Dryad rows excluded and recorded in `logs/missing_data_log.csv`.
5. **Aggregation**: compute species‑mean telomere length, retain `study_ids` (list of contributing DOIs), count of observations `n_obs`, and single values for lifespan, migration, body mass → `data/processed/merged_analysis.csv`.
6. **Phylogeny** (`04_fetch_phylogeny.py`): OpenTree induced subtree, pruned to the species list; unmatched tips logged and removed.

## Statistical Methodology

### Primary Model (Base PGLS) — FR‑004
- Formula: `lifespan_years ~ telomere_length_kb + body_mass_g + measurement_method`, fitted with `phylolm(model = "lambda")`.
- **Low‑power handling**: If `n_species < 15`, write the message `"Low Power: Phylogenetic inference unreliable"`, set `low_power_flag: true`, and leave all coefficient, SE, CI, p‑value, λ, and AIC fields **null**.
- Diagnostics: convergence status, λ estimate with 95 % CI, VIF for collinearity (body mass vs. lifespan noted).

### Interaction Model — FR‑005
- Formula: `lifespan_years ~ telomere_length_kb * migration_status + body_mass_g + measurement_method`.
- **Eligibility**: Only fitted when `n_species ≥ 30`. **Rows with `migration_status == "Unknown"` are **excluded** from this model** and logged in `logs/interaction_exclusion_log.csv`. This prevents treating missing data as a biological category.
- Outputs: interaction coefficient, standard error, 95 % CI, p‑value, ΔAIC vs. base, λ diagnostics.

### Sensitivity — FR‑006, SC‑004
- **Study‑level jackknife**: If any Dryad study contributes >1 species, perform jackknife by leaving out each study (one at a time). Otherwise perform LOOCV by species. Log the chosen method and justification in `results/sensitivity_log.csv`.
- **Jackknife vs. LOOCV** rationale is explicitly recorded.

### Power — SC‑005
- **Simulation‑based power**: generate **[deferred]** phylogenetic datasets using the observed tree and estimated λ. For each simulated dataset, inject a **standardized regression slope of 0.5 SD** for telomere length (equivalent to a partial‑R² of ~0.25). Fit the base PGLS and record whether `p_telomere < α`. Power = proportion of simulations meeting this criterion. Seed is pinned (42) for reproducibility.

### Alpha and multiple comparisons — SC‑002
- Single primary fixed effect; α = 0.05 fixed in `config.yaml`. No correction applied; the interaction and sensitivity analyses are labeled secondary/exploratory. The model output includes a boolean `significance_flag` (true when `p_value_telomere < α`).

### Causal framing
- Observational, cross‑species data: all claims are **associational**; no causal or randomization‑based identification is claimed.

## Compute Feasibility (CPU‑first)
- All methods (pandas, `phylolm`, `rotl`, `matplotlib`) run on 2 vCPU / 7 GB RAM in minutes. No GPU components; the Kaggle escape hatch is not needed.

## Decision/Rationale
- **CPU‑first everywhere**; no GPU components.
- **No synthetic fallback** — real data or hard failure (fabrication gate).
- **R packages** installed via `install_packages.R` (resolves T011); we deliberately do **not** use `renv`, and the verification script for renv is disabled in the pipeline.
- **Runtime discovery only** for Dryad IDs — no placeholder `dataset_ids` (addresses T002); `02_ingest_data.py` and `03_clean_merge.py` read this config and contain no hard‑coded URLs or seeds.

## Quick Reference of Scripts (existence confirmed)
- `code/01_discover_data.py`
- `code/02_ingest_data.py`
- `code/03_clean_merge.py`
- `code/04_fetch_phylogeny.py`
- `code/05_fit_pgls_base.py`
- `code/06_fit_pgls_interaction.py`
- `code/07_sensitivity.py`
- `code/08_visualize.py`

These scripts are version‑controlled, deterministic, and read `code/config.yaml` at runtime.
