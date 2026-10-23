# Tasks: Investigating the Correlation Between Dietary Fiber Intake and Gut Microbiome Composition  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and any existing checked artifacts.  
All tasks write to project‑owned paths under `data/`, `results/`, or `code/`.  
Tasks are ordered to respect data flow; later tasks depend on the outputs of earlier ones.

---

## Phase 1 – Data acquisition & harmonisation (US‑1, priority P1)

- [ ] **T001** `[US-1]` **Download American Gut Project (AGP) raw 16S tables & metadata**  
  *File*: `code/src/ingestion/agp_loader.py`  
  *Action*: Use `datasets.load_dataset("american_gut/agp_diet", streaming=True)` to stream the data, write the raw files to `data/raw/agp/` (e.g., `agp_counts.tsv`, `agp_metadata.tsv`). Generate SHA‑256 checksums stored in `data/state/agp_checksums.json`.  
  *Verification*: Run `python -m code.src.ingestion.agp_loader` and confirm both files exist, are non‑empty, and the checksum file contains two entries.

- [ ] **T002** `[US-1]` **Download UK Biobank (UKBB) raw 16S tables & metadata – required cohort**  
  *File*: `code/src/ingestion/ukbb_loader.py`  
  *Action*: Load `datasets.load_dataset("ukbiobank/gut_microbiome", streaming=True)`. Write raw files to `data/raw/ukbb/` (`ukbb_counts.tsv`, `ukbb_metadata.tsv`) and record SHA‑256 checksums in `data/state/ukbb_checksums.json`. **If the dataset is unavailable, raise a RuntimeError indicating that UKBB is mandatory; no fallback dataset is permitted.**  
  *Verification*: Execute the script; both raw files must be present and checksum file populated. Failure to fetch UKBB aborts the pipeline, satisfying FR‑001.

- [ ] **T003** `[US-1]` **Harmonise and filter the two cohorts**  
  *File*: `code/src/preprocessing/harmonizer.py`  
  *Action*:  
  1. Load the raw count and metadata files from AGP and UKBB.  
  2. Convert any fiber‑intake unit to **g/day**.  
  3. Keep only samples with `read_depth ≥ 5 000` and `0 ≤ fiber_intake_g ≤ 200`.  
  4. Add a `cohort` column (`AGP` or `UKBB`).  
  5. Write the unified, filtered table to `data/processed/harmonized.tsv`.  
  *Verification*: Run the script and then validate `data/processed/harmonized.tsv` against `contracts/dataset.schema.yaml` using the provided pytest contract test.

- [ ] **T003a** `[US-1]` **Verify unified dataset meets minimum sample‑size**  
  *File*: `code/src/preprocessing/sample_size_check.py`  
  *Action*: Count total rows in `data/processed/harmonized.tsv`; assert `>= 1000`. Write a short report `results/state/sample_size_report.txt`.  
  *Verification*: CI fails if the count is < 1000, satisfying SC‑007.

- [ ] **T004** `[US-1]` **Handle missing covariates**  
  *File*: `code/src/preprocessing/covariate_cleaner.py`  
  *Action*:  
  1. Exclude samples with > 20 % missing covariate values (age, BMI, antibiotic_use, sex, batch).  
  2. Median‑impute numeric covariates; mode‑impute categorical covariates.  
  3. Output the cleaned dataset to `data/processed/harmonized_clean.tsv`.  
  *Verification*: After execution, check that no column contains `NaN` and that the number of rows matches the log file `data/state/covariate_exclusion.log`.

---

## Phase 2 – Compositional transformation & primary association (US‑2, priority P2)

- [ ] **T005** `[US-2]` **Apply Bayesian‑multiplicative replacement + CLR transformation to taxon counts**  
  *File*: `code/src/preprocessing/clr_transform.py`  
  *Action*:  
  1. Read `data/processed/harmonized_clean.tsv`.  
  2. Add a pseudocount of `1e‑6` to zero‑inflated taxa (using `zCompositions::cmultRepl`).  
  3. Perform centred‑log‑ratio (CLR) transformation on the taxon matrix.  
  4. Save the CLR matrix to `data/processed/clr_matrix.tsv`.  
  *Verification*: Confirm that the file contains no `NaN`/`Inf` values and that the first few rows are printed in the log `data/state/clr_log.txt`.

- [ ] **T006** `[US-2]` **Spearman correlation (with bootstrap SE) and BH FDR correction**  
  *File*: `code/src/analysis/spearman_bootstrap.py`  
  *Action*:  
  1. Compute residuals of fiber intake and each CLR taxon after regressing out covariates (`age`, `BMI`, `sex`, `antibiotic_use`, `read_depth`).  
  2. Calculate Spearman ρ for each taxon (`scipy.stats.spearmanr`).  
  3. Estimate standard error via 1 000 non‑parametric bootstrap resamples.  
  4. Apply Benjamini‑Hochberg FDR correction to the raw p‑values, producing q‑values.  
  5. Write results to `results/association/spearman.tsv` with columns matching `correlation_result.schema.yaml` (`taxon`, `spearman_rho`, `spearman_se`, `raw_p_value`, `q_value`, `significant`).  
  *Verification*: Run the script and then validate the TSV against `contracts/correlation_result.schema.yaml`.

- [ ] **T007** `[US-2]` **MaAsLin2 multivariable association on CLR data with BH correction**  
  *File*: `code/src/analysis/maaslin2_association.R` (invoked via `rpy2`)  
  *Action*:  
  1. Feed `data/processed/clr_matrix.tsv` and the cleaned metadata (`harmonized_clean.tsv`) to MaAsLin2, adjusting for `age`, `BMI`, `sex`, `antibiotic_use`, and `read_depth`.  
  2. Export beta coefficients, raw p‑values, and apply Benjamini‑Hochberg FDR correction to obtain q‑values.  
  3. Write to `results/association/maaslin2.tsv` with columns `taxon`, `beta_coefficient`, `raw_p_value`, `q_value`, `significant`.  
  *Verification*: After execution, merge with the Spearman file (see T008) and run the contract test on the merged TSV.

- [ ] **T008** `[US-2]` **Merge Spearman and MaAsLin2 results into a single association table**  
  *File*: `code/src/analysis/merge_association.py`  
  *Action*: Join `spearman.tsv` and `maaslin2.tsv` on `taxon`, keep all required fields, add a `cohort` column derived from the original sample metadata, and output `results/association/association_combined.tsv`.  
  *Verification*: Validate the merged file against `contracts/correlation_result.schema.yaml` (all required fields present).

---

## Phase 3 – Differential abundance & cross‑cohort validation (US‑3, priority P3)

- [ ] **T009** `[US-3]` **Define high‑ and low‑fiber groups per cohort (75th / 25th percentiles)**  
  *File*: `code/src/analysis/fiber_groups.py`  
  *Action*: Compute cohort‑specific quartiles on `fiber_intake_g`, assign samples to `high` or `low` groups, and write a mapping file `data/processed/fiber_group_assignments.tsv`.  
  *Verification*: Assert that for each cohort `high` count == floor(0.25 * cohort_size) and `low` count == floor(0.25 * cohort_size). Fail the task if the counts differ.

- [ ] **T010** `[US-3]` **ANCOM‑II on relative abundances (per cohort)**  
  *File*: `code/src/analysis/ancom2.R` (called via `rpy2`)  
  *Action*:  
  1. Convert CLR‑transformed values back to relative abundances.  
  2. Run ANCOM‑II separately for AGP and UKBB using the high/low group assignments.  
  3. Output `results/differential/ancom_agp.tsv` and `results/differential/ancom_ukbb.tsv` with columns `taxon_id`, `method`, `q_value`, `effect_size`, `direction`.  
  *Verification*: Each TSV must pass `contracts/diff_abundance.schema.yaml`.

- [ ] **T011** `[US-3]` **DESeq2 on CLR‑transformed data (per cohort)**  
  *File*: `code/src/analysis/deseq2_clr.R` (called via `rpy2`)  
  *Action*:  
  1. Use the CLR‑transformed matrix (`data/processed/clr_matrix.tsv`) as continuous input to DESeq2 (treating CLR values as expression‑like measurements).  
  2. Run DESeq2 with the high/low group design for each cohort.  
  3. Write `results/differential/deseq2_agp.tsv` and `results/differential/deseq2_ukbb.tsv` matching the diff‑abundance schema.  
  *Verification*: Contract validation against `contracts/diff_abundance.schema.yaml`.

- [ ] **T012** `[US-3]` **Cross‑cohort replication flagging (per‑taxon)**  
  *File*: `code/src/analysis/cross_cohort_replication.py`  
  *Action*:  
  1. For each taxon‑method pair, check whether `q_value < 0.05` in **both** cohorts and whether `direction` matches.  
  2. Add a boolean column `replicated` (true/false).  
  3. Produce a unified file `results/differential/replication_status.tsv`.  
  *Verification*: Confirm the presence of a boolean `replicated` column, and that its values follow the defined logic.

- [ ] **T012b** `[US-3]` **Compute overall cross‑cohort replication rate**  
  *File*: `code/src/analysis/replication_rate.py`  
  *Action*: Read `replication_status.tsv`, calculate the percentage of taxa that are replicated (both cohorts significant with same direction), and write `results/summary/replication_rate.txt` (e.g., `Replication rate: 57.32%`).  
  *Verification*: The file must contain a single line matching the regex `Replication rate: \d+\.\d{2}%`.

- [ ] **T013** `[US-3]` **Calculate absolute median fiber intake for high/low groups**  
  *File*: `code/src/analysis/fiber_medians.py`  
  *Action*: Compute median `fiber_intake_g` for the high‑ and low‑fiber groups within each cohort and write `results/summary/fiber_medians.tsv` (columns: `cohort`, `group`, `median_fiber_g`).  
  *Verification*: Ensure exactly two rows per cohort (`high` and `low`) and that each `median_fiber_g` lies within 0–200 g/day.

---

## Phase 4 – Measurement‑error simulation & power analysis (supporting US‑2)

- [ ] **T014** `[US-2]` **Synthetic measurement‑error simulation**  
  *File*: `code/src/simulation/measurement_error.py`  
  *Action*:  
  1. Generate a synthetic dataset with known β = 0.1 for a subset of taxa.  
  2. Add Gaussian noise (SD = 10 % of mean fiber) to the fiber vector.  
  3. Run the same Spearman + MaAsLin2 pipelines (reuse T006‑T008).  
  4. Report median absolute bias (|estimated − true| / true) in `results/simulation/measurement_error_report.tsv`.  
  *Verification*: The report contains a column `bias` and the median is ≤ 0.10.

- [ ] **T015** `[US-2]` **A‑priori power analysis for both statistical components**  
  *File*: `code/src/power/power_analysis.py`  
  *Action*:  
  1. Use `statsmodels.stats.power.CorrelationPower` to compute required sample size for detecting ρ ≈ 0.15 at α = 0.05, 80 % power (Spearman component).  
  2. Use `statsmodels.stats.power.FTestPower` for the MaAsLin2 linear model (effect size β = 0.1).  
  3. Write a summary `results/power/power_requirements.tsv` (columns: `test`, `required_n`, `achieved_n`, `power`).  
  4. If the achieved power for either cohort falls below 0.8, write a warning file `results/power/power_warning.txt` and **halt downstream analyses** (tasks T010‑T013 must read this flag and, if present, add a `power_flag = "underpowered"` column to their outputs).  
  *Verification*: Run the script; the warning file appears only when appropriate and contains the cohort name(s).

---

## Phase 5 – Visualisation & final reporting

- [ ] **T016** `[US-3]` **Volcano plots for ANCOM‑II and DESeq2**  
  *File*: `code/src/visualisation/volcano_plots.R` (called via `rpy2`)  
  *Action*: Generate two PNG files (`results/figures/volcano_ancom.png`, `results/figures/volcano_deseq2.png`) showing –log10(q) vs. effect size, colour‑coded by significance.  
  *Verification*: Files exist, are non‑empty, and the script prints the number of significant points.

- [ ] **T017** `[US-2]` **CLR‑based PCA ordination coloured by fiber quartile**  
  *File*: `code/src/visualisation/pca_clr.R` (called via `rpy2`)  
  *Action*: Perform PCA on the CLR matrix, colour points by high/low fiber group per cohort, and save `results/figures/pca_clr_agp.png` and `results/figures/pca_clr_ukbb.png`.  
  *Verification*: PNGs exist and the proportion of variance explained is logged.

- [ ] **T018** `[US-3]` **Assemble final summary table**  
  *File*: `code/src/report/final_summary.py`  
  *Action*: Merge:  
    - `association_combined.tsv` (T008)  
    - Differential‑abundance files (`ancom_*.tsv`, `deseq2_*.tsv`)  
    - `replication_status.tsv` (T012)  
    - `replication_rate.txt` (T012b)  
    - `fiber_medians.tsv` (T013)  
    - Power information (`power_requirements.tsv`, `power_warning.txt` if present)  
    Produce `results/final_summary.tsv` containing for each taxon: method, q‑value, effect size, direction, replicated flag, median fiber values for both cohorts, and a `power_flag` column when applicable.  
  *Verification*: The file contains all required columns, passes a custom schema test (`tests/contract/test_final_summary_schema.py`), and the first few rows are printed in the log.

- [ ] **T019** `[US-3]` **Generate markdown report linking all artefacts**  
  *File*: `docs/report.md`  
  *Action*: Auto‑populate a markdown document that (a) describes methods, (b) lists key tables with file paths, (c) embeds the PNG figures, and (d) summarises the replication rate and power analysis outcome.  
  *Verification*: Render the markdown with `pandoc` in a CI step; the resulting HTML contains all figures and tables.

---

## Phase 6 – Verification & reproducibility (continuous)

- [ ] **T020** `Contract‑based unit tests`  
  *File*: `tests/contract/` (existing)  
  *Action*: Run `pytest -q tests/contract` after every major task. All tests must pass before the next phase begins.  
  *Verification*: CI step reports “0 failures”.

- [ ] **T021** `Determinism check`  
  *File*: `code/src/utils/determinism_check.py`  
  *Action*: Run the full pipeline twice with the same random seed, compute SHA‑256 hashes of all files under `results/`, and write a comparison report `results/state/determinism_report.txt`.  
  *Verification*: The report states “All hashes match” → pipeline is deterministic.
