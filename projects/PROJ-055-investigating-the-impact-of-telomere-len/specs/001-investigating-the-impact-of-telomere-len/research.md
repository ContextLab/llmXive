# Research: Investigating the Impact of Telomere Length on Lifespan Variation in Wild Bird Populations

## Executive Summary
This research document defines the data acquisition, statistical methodology, and compute plan for testing whether early‑life telomere length predicts maximum lifespan in wild birds, and whether migration status moderates that relationship. Because the required Dryad and AnAge datasets lack verified public URLs, the pipeline includes a deterministic synthetic data generator that respects the exact schema required for downstream analysis. When real data become available, the same pipeline will ingest them without code changes.

## Construct Validity Disclaimer (expanded)
The analysis uses **species‑mean early‑life telomere length** and **maximum recorded lifespan** as proxies for the underlying biological constructs. This aggregation is necessitated by the nature of the publicly available data (most studies report species‑level summaries rather than individual‑level paired measurements). While this species‑level approach reduces within‑species variance, it may introduce bias if a few individuals disproportionately influence the species mean or if captive lifespan records inflate the maximum lifespan.

To mitigate these threats we:

1. **Filter** for wild‑caught individuals only before aggregation.  
2. **Perform outlier diagnostics** on species means (e.g., median‑absolute‑deviation trimming) and log any excluded species.  
3. **Run a supplementary mixed‑effects model** (if any dataset contains individual‑level paired telomere–lifespan records) to assess whether the species‑level aggregation distorts the effect size.  
4. **Execute a jackknife/LOOCV sensitivity analysis** (see FR‑006) that recomputes the telomere‑lifespan coefficient after removing each species in turn, reporting the range of coefficients.  
5. **Explicitly report** this limitation in the final results summary, framing all conclusions as **associational** at the species level.

## Dataset Strategy

### 1. Data Discovery (Phase 0) & A‑Priori Power Planning
- **Dryad**: Query the Dryad Search API for records containing `"telomere"` + `"bird"` + `"wild"`. The script records any returned dataset DOIs in `config.yaml` under `dataset_ids`.  
- **AnAge**: Download the latest `anage.csv` export from the AnAge website (public CSV).  
- **Power Planning**: Prior to any modeling we compute the required number of species to achieve **≥ 0.80 power** to detect a **moderate effect** (Cohen’s d = 0.5) at α = 0.05 using the R `pwr` package (simulation‑based for phylogenetic models). The calculation yields **≥ 30 species** as the target. If the merged species count after Phase 2 is **< 30**, the pipeline aborts with a **Low‑Power** error and logs the shortfall in `results/run_summary.yaml`.  
- **Failure Condition**: No DOI or download error → log **Data Availability Error** and switch to synthetic data generation (`synthetic_data.py`).

### 2. Raw Data Sources (Verified URLs)
| Type | URL(s) | Note |
|------|--------|------|
| TRF reference tables (human, for unit‑conversion illustration) | `<br>`<br>` | Verified in the “# Verified datasets” block; used only to demonstrate conversion logic. |
| Dryad & AnAge | *No verified URLs* – see Data Availability section. | The pipeline will **not** fabricate URLs; it will either fetch via the public API or generate synthetic data. |

### 3. Integration Plan
1. **Ingestion** (`02_ingest_data.py`) reads each Dryad CSV into a pandas DataFrame, records SHA‑256 checksums, and writes raw files under `data/raw/`.  
2. **Standardization** (`03_clean_merge.py`)  
   - Detects `telomere_length` column units (`kb`, `bp`, or `Ct`).  
   - Converts `bp` → `kb` (divide by 1 000).  
   - For `Ct` values, looks for a `standard_curve` column; if absent, flags the row as *unconvertible* and writes to `logs/unconvertible_units.csv`.  
   - Filters rows where `age_category` is `"Juvenile"` (or equivalent).  
   - Logs every conversion in `logs/unit_conversion_log.csv`.  
   - Populates all schema fields (e.g., `study_id`, `provenance_source`) for every record.  
3. **Merging** – left‑join on `species_name` (case‑insensitive, stripped of whitespace).  
   - Unmatched Dryad rows → excluded, recorded in `logs/missing_data_log.csv`.  
   - Unmatched AnAge rows → ignored (no telomere data).  
4. **Aggregation** – compute species‑mean telomere length (`telomere_length_kb`) and retain single values for `lifespan_years`, `migration_status`, `body_mass_g`. Output `data/processed/merged_analysis.csv`.  

### 4. Phylogeny Acquisition
- Use the R `rotl` package to query the Open Tree of Life for the exact species list.  
- Retrieve the induced subtree in Newick format and store as `data/phylogeny/bird_tree.nwk`.  
- The tree is pruned to match the species in `merged_analysis.csv`; any missing tip triggers a warning and removal of that species (also logged).

### 5. Synthetic Data (Fallback)
If Phase 0 fails, `synthetic_data.py` creates a reproducible CSV with:
- 30 species (`Species_01` … `Species_30`).  
- Telomere lengths drawn from `Normal(5 kb, 1 kb)`.  
- Lifespan drawn from `Normal(10 yr, 3 yr)` with a modest positive correlation (r ≈ 0.4).  
- Randomly assigned `migration_status` and realistic body mass values (log‑normal distribution).  
- **Provenance**: Records are tagged as `provenance_source = "Synthetic-Dryad"` or `"Synthetic-AnAge"` to ensure schema compliance.  
All random seeds are pinned (`seed=42`). The synthetic file conforms exactly to `contracts/dataset.schema.yaml`.

## Statistical Methodology

### A Priori Power Justification (see Phase 0)
To detect a moderate effect size (Cohen's d = 0.5) with α = 0.05 and target power ≥ 0.80, we require **≥ 30 species** for a phylogenetic GLS. The pipeline aborts if the merged dataset contains fewer species, ensuring adequate power before any inference (addresses SC‑005).

### Construct Validity (see disclaimer above)
Species‑level aggregation is a necessary compromise; we treat results as associational and report the aggregation limitation alongside sensitivity analyses.

### Primary Model (Base PGLS)
- **Formula**: `lifespan_years ~ telomere_length_kb + body_mass_g + measurement_method`.  
- **Implementation**: R `phylolm::phylolm()` with `model = "lambda"` (estimates Pagel’s λ). The phylogenetic covariance is incorporated via the error structure, not as a predictor.  
- **Assumptions**:  
  - Observational association only (Principle VII).  
  - Linear relationship on the raw scale.  
  - No high collinearity (VIF checked; if VIF > 5, report descriptive correlation and proceed with caution).  
- **Diagnostics**: Convergence status, λ confidence interval, residual normality (Shapiro‑Wilk).  

### Interaction Model (Moderator)
- **Formula**: `lifespan_years ~ telomere_length_kb * migration_status + body_mass_g + measurement_method`.  
- **Low‑Power Guard**: If `n_species < 30`, the interaction model is **skipped** and a flag `interaction_skipped_low_power = true` is written to `model_summary.csv`.  

### Sensitivity Analysis (FR‑006)
- **LOOCV**: Iteratively drop one species, refit the base model, record the telomere coefficient.  
- **Jackknife**: If `n_species < 10`, drop one study (identified by `study_id`) instead.  
- **Output**: `results/sensitivity_log.csv` with coefficient range and stability metric (e.g., coefficient SD).  

### Power & Sample‑Size (SC‑005)
- Perform a **simulation‑based power analysis** for the final species count using the R `pwr` package: generate 1 000 simulated datasets with the observed effect size, fit PGLS, and compute the proportion with p < 0.05.  
- Record `power_estimate` (0 – 1) in `model_summary.csv`.  
- If `power_estimate < 0.8`, automatically add a **Low Power** warning to `results/run_summary.yaml`.  

### Multiple‑Comparison & Alpha (SC‑002)
- Only a single primary hypothesis (telomere → lifespan) is tested; no correction required per the specification.  
- Alpha threshold is fixed at **0.05** (documented in `config.yaml`).  

## Compute Feasibility (CPU‑first)
- **Memory**: All pandas DataFrames ≤ 200 MB; R covariance matrix ≤ 500 × 500 ≈ 2 MB.  
- **CPU**: Linear operations; total CPU time < 15 min on 2 vCPU.  
- **Disk**: Raw + processed CSVs < 500 MB; phylogeny < 5 MB.  

## projects/PROJ-055-investigating-the-impact-of-telomere-len/specs/001-investigating-the-impact-of-telomere-len/state/projects/PROJ-055...yaml
*Updated automatically by `utils.py` after each step to record SHA‑256 hashes and the `run_summary` flag (real vs. synthetic data).*
