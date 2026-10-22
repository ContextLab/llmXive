# Tasks: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets  

**Input**: `spec.md`, `plan.md`, `data-model.md`, contracts, and existing artifacts.  

**Organization**: Tasks are grouped by research phase and user story.  Checked boxes (`[X]`) indicate work that has already been verified as correct.  Unchecked boxes (`[ ]`) are pending implementation or revision.  All tasks follow the canonical format  

```
- [ ] T### [P] [USx] description … with file path
  • <indented continuation lines for requirements, verification, etc.>
```  

---

## Phase 0 – Data Feasibility Check (Blocking Gate)

- [X] T000a [P] [US1] Implement `code/data_feasibility.py` to query verified public sources for a dataset that contains both 16S rRNA data **and** PHQ‑9/GAD‑7 scores, returning `results/feasibility_check.json`.  
  • Verify that the JSON file exists and contains a boolean `data_available` field.  

- [X] T000b [P] [US1] If no linked dataset is found, generate a “Data Gap Report” at `results/data_gap_report.md` (JSON/Markdown) and halt the pipeline.  
  • Verify that `results/data_gap_report.md` is created and contains the required “Data Gap” statement.  

- [ ] T000c [P] [US1] Log a confirmation message and allow the pipeline to continue when a suitable dataset is discovered.   <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 -->
  • Verify that the log entry `Data feasibility confirmed` appears in `logs/pipeline.log`.  

---

## Phase 1 – Project Setup (Shared Infrastructure)

- [ ] T001a [P] Create data directories: `mkdir -p data/raw/ data/processed/ data/interior/`.  
  • Verify that each directory exists after execution.  

- [X] T001b [P] Create code directories: `mkdir -p code/ code/models/ code/utils/`.  
  • Verify that each directory exists after execution.  

- [X] T001c [P] Create test directories: `mkdir -p tests/unit/ tests/integration/ tests/contract/`.  
  • Verify that each directory exists after execution.  

- [ ] T002a [P] Add `requirements.txt` with pinned versions for core dependencies (pandas, scikit‑learn, scipy, numpy, biom-format, scikit‑bio, matplotlib, seaborn, requests, pytest, statsmodels).  
  • Verify that `requirements.txt` contains at least the listed packages and that `pip install -r requirements.txt` succeeds without errors.  

- [ ] T002b [P] Implement `code/scripts/generate_lock.py` to produce `requirements.lock` from `requirements.txt`.  
  • Verify that `requirements.lock` is generated and matches the installed package versions.  

- [ ] T002c [P] Implement `code/seeds.py` that writes `state/seeds.yaml` containing `random_seed`, `numpy_seed`, and (if applicable) `torch_seed`.  
  • Verify that `state/seeds.yaml` exists and contains three integer entries.  

---

## Phase 2 – Foundational Infrastructure (Blocking Prerequisites)

- [ ] T004 [P] Implement `code/config.py` with global paths, random seeds, and thresholds (0.1 % prevalence, 20 % rarefaction‑loss cutoff).  
  • Verify that `code/config.py` can be imported and that all constants are defined.  

- [~] T005 [P] Implement logging in `code/utils/logging.py` that writes to `logs/pipeline.log` with rotation.  
  • Verify that after running any script, `logs/pipeline.log` is created and contains timestamped entries.  

- [~] T006 [P] Define data‑model classes (`MicrobiomeSample`, `MentalHealthRecord`, `AssociationResult`) in `code/models.py`.  
  • Verify that `code/models.py` can be imported and that each class has the required attributes.  

- [~] T007 [P] Add a `.env` file at the repository root containing required environment variables (e.g., `AGP_STUDY_ID=10317`, `DATA_URL=…`). Implement loading logic in `code/config.py` using `python-dotenv` so that all scripts obtain configuration from `os.getenv`. Verify that `code/config.py` raises a clear `RuntimeError` if any required variable is missing.  
  • Verify that `.env` exists, that `python-dotenv` loads the variables, and that missing variables cause a RuntimeError with an informative message.  

- [~] T008 [P] Implement streaming merge in `code/data_ingestion.py`: `streaming_merge_otu_metadata` reads the OTU table and metadata via `datasets.load_dataset(..., streaming=True)`, yields merged chunks, and raises `MemoryError` if a full load is attempted.  
  • Verify that attempting to load the full dataset without streaming raises `MemoryError`.  

- [ ] T009 [P] Extend `code/data_ingestion.py` so that any network‑related exception (e.g., 404, timeout) triggers the Data Gap Report generation (same logic as T000b) and **exits gracefully** without producing placeholder data.   <!-- FAILED-IN-EXECUTION: code/data_ingestion.py exit=1 -->
  • Verify that a simulated network failure results in `results/data_gap_report.md` being written and that the script exits with a non‑zero status.  

- [ ] T010 [Write] Write unit tests in `tests/unit/test_preprocessing.py` for rarefaction‑fallback logic, median‑depth calculation, and missing‑value filtering.  
  • Verify that `pytest tests/unit/test_preprocessing.py` runs and all tests pass.  

- [ ] T011 [Write] Write unit tests in `tests/unit/test_data_ingestion.py` for streaming‑merge chunk size, memory‑limit enforcement, and retry‑with‑exponential‑backoff on rate‑limited API calls.  
  • Verify that `pytest tests/unit/test_data_ingestion.py` runs and all tests pass.  

---

## Phase 3 – User Story 1: Data Acquisition & Preprocessing (Priority P1)

- [ ] T012 [US1] Implement `code/data_ingestion.py` to download the AGP dataset (Study 10317) via the Qiita API or a verified HuggingFace mirror, apply exponential‑backoff retries, merge OTU and metadata on `sample_id`, and write the merged raw file to `data/raw/merged_raw.parquet`.  
  • Verify that `data/raw/merged_raw.parquet` exists, has ≥ 100 rows, and contains no missing `sample_id`.  

- [ ] T012b [US1] Extend the same script to compute SHA‑256 checksums for all downloaded raw files, write them to `data/raw/checksums.txt`, and update the project `state.yaml` (located at `state/projects/PROJ-215-.../state.yaml`) with these hashes under an `artifact_hashes` map.  
  • Verify that `data/raw/checksums.txt` contains one line per file, and that `state.yaml` includes matching hash entries.  

- [ ] T013 [US1] Filter out samples lacking PHQ‑9 or GAD‑7 scores, log the exclusion rate, and write the filtered OTU table to `data/interior/filtered_otu_table.biom`.  
  • Verify that `data/interior/filtered_otu_table.biom` exists and that the log records the exclusion percentage.  

- [ ] T014a [US1] Implement `code/preprocessing.py` function `calculate_median_depth` that reads `data/interior/filtered_otu_table.biom`, computes the sum of counts per sample, determines the median, and writes `data/interior/median_depth.json` (schema: `{ "median_depth": <int> }`).  
  • Verify that `data/interior/median_depth.json` exists and contains a positive integer.  

- [ ] T014b [US1] Implement `code/preprocessing.py` function `estimate_rarefaction_loss` that loads `data/interior/median_depth.json`, simulates rarefaction to that depth on the filtered OTU table, calculates the proportion of samples that would be dropped, and writes `data/interior/estimated_loss.json` (schema: `{ "loss_rate": <float>, "samples_lost": <int> }`).  
  • Verify that `data/interior/estimated_loss.json` exists and that `loss_rate` is between 0 and 1.  

- [ ] T014d [US1] Implement the variance‑stabilizing transformation (VST) routine (e.g., using `skbio.stats.composition.clr`) in `code/preprocessing.py`.  
  • Verify that the VST function returns a biom table and can be called without error.  

- [ ] T014e [US1] Implement the rarefaction routine (e.g., using `skbio.diversity.subsample_counts`) in `code/preprocessing.py`.  
  • Verify that the rarefaction function returns a biom table and can be called without error.  

- [ ] T014c [US1] Extend `code/preprocessing.py` with logic that reads `estimated_loss.json`; if `loss_rate > 0.20` apply VST, otherwise perform rarefaction to the median depth. Write the resulting pre‑processed OTU table to `data/processed/preprocessed_otu_table.biom`.  
  • Verify that `data/processed/preprocessed_otu_table.biom` exists and that the chosen method matches the loss rate condition.  

- [ ] T015 [US1] Filter out taxa whose prevalence across samples is < 0.1 % on the pre‑processed OTU table, writing the result to `data/processed/filtered_otu_table.biom`.  
  • Verify that `data/processed/filtered_otu_table.biom` exists and that all retained taxa have prevalence ≥ 0.1 %.  

- [ ] T016 [US1] Compute alpha‑diversity (Shannon and Simpson) for each sample from `filtered_otu_table.biom` and write `data/processed/alpha_metrics.csv`.  
  • Verify that `alpha_metrics.csv` contains columns `sample_id`, `alpha_shannon`, `alpha_simpson` with no missing values.  

- [ ] T016b [US1] Compute beta‑diversity:  
  • Bray‑Curtis distance matrix → `data/processed/bray_curtis.npz`  
  • Weighted UniFrac (if `data/raw/tree.nwk` exists) → `data/processed/weighted_unifrac.npz` (or a “skipped” flag file)  
  • Unweighted UniFrac (if tree exists) → `data/processed/unweighted_unifrac.npz` (or a “skipped” flag file).  
  • Verify that each `.npz` file exists when applicable and that a corresponding “skipped” flag file is created when the tree is absent.  

- [ ] T017 [US1] Merge alpha metrics with the filtered metadata to produce `data/processed/cleaned_dataset.csv`. Verify that at least 80 % of the originally downloaded samples remain and that the file contains ≥ 100 rows with *no* missing values in `phq9_score`, `alpha_shannon`, `alpha_simpson`. Write a summary of retention statistics to `data/processed/metrics.json`.  
  • Verify that `cleaned_dataset.csv` meets the row‑count and completeness criteria and that `metrics.json` records `retention_rate` ≥ 0.80.  

- [ ] T010x [Execute] Run the unit tests from T010 against the implemented preprocessing functions.  
  • Verify that `pytest -q tests/unit/test_preprocessing.py` exits with 0 failures.  

- [ ] T011x [Execute] Run the unit tests from T011 against the streaming ingestion logic.  
  • Verify that `pytest -q tests/unit/test_data_ingestion.py` exits with 0 failures.  

---

## Phase 4 – User Story 2: Statistical Association Analysis (Priority P2)

- [ ] T020 [US2] Implement `code/analysis.py` to compute partial Spearman correlations between (a) alpha‑diversity metrics and PHQ‑9/GAD‑7 scores, and (b) each taxon’s abundance and the same scores, adjusting for age and BMI when present. Write raw p‑values to `data/interim/unadjusted_alpha_pvals.csv` and `data/interim/unadjusted_taxa_pvals.csv`.  
  • Verify that both CSV files exist, contain a `p_value` column with values in [0,1], and that the number of rows matches the number of tested features.  

- [ ] T021a [US2] In `code/analysis.py`, create a binary `depression_group` column (`PHQ‑9 ≥ 10` → “High”, else “Low”) and write `data/interim/grouping_variables.csv`.  
  • Verify that the CSV contains `sample_id` and `depression_group` columns with only “High”/“Low” values.  

- [ ] T021 [US2] Perform PERMANOVA on the Bray‑Curtis matrix (`data/processed/bray_curtis.npz`) using the grouping variable, adjusting for age and BMI, and write results to `data/interim/permanova_bray_curtis.csv`.  
  • Verify that the CSV contains `p_value` and `F_statistic` columns and that `p_value` ∈ [0,1].  

- [ ] T021b [US2] If UniFrac matrices exist, perform PERMANOVA on each and write `data/interim/permanova_weighted_unifrac.csv` and `data/interim/permanova_unweighted_unifrac.csv`; otherwise log a skip message.  
  • Verify that either the CSV files are created or a log entry indicating the skip is present.  

- [ ] T022a [US2] Apply Benjamini‑Hochberg correction to **all** raw p‑values from T020 (both alpha and taxa) and write `data/interim/adjusted_pvals.csv` (columns: `feature`, `pval_raw`, `pval_adj`).  
  • Verify that `pval_adj` ≤ 1 for every row and that the file includes all features from T020.  

- [ ] T022c [US2] Export the PERMANOVA p‑values (which are single global tests) unchanged to `data/processed/permanova_final.csv`.  
  • Verify that the CSV contains the PERMANOVA results with correct column names.  

- [ ] T023a [US2] **SC‑005 Check** – Compute `|p_adj – p_raw|` for every taxon, identify the maximum delta, and write `results/covariate_delta.json` containing `{ "max_delta": <float>, "threshold_met": <bool> }` (threshold = 0.01).  
  • Verify that `max_delta` is a non‑negative float and that `threshold_met` is `true` when the max delta ≤ 0.01.  

- [ ] T024 [US2] **SC‑002 Check** – If no taxa are significant after BH correction (`q < 0.05`), run a Kolmogorov‑Smirnov test of the raw p‑value distribution against Uniform[0,1]; write `data/processed/ks_test_results.json` with `{ "statistic": <float>, "p_value": <float>, "result": "PASS"/"FAIL" }`.  
  • Verify that the JSON file is created and that `result` is “PASS” when `p_value` < 0.05.  

- [ ] T025 [US2] Produce the final association table `data/processed/association_results.csv` containing variable name, correlation coefficient, raw p‑value, BH‑adjusted p‑value, `p_value_delta`, effect direction, covariates used, and a boolean `significant` flag.  
  • Verify that the CSV conforms to `specs/001‑investigating‑the‑relationship‑between‑g/contracts/output.schema.yaml` (all required fields present, correct types, and `significant` is true iff `adjusted_p_value` < 0.05).  

---

## Phase 5 – User Story 3: Visualization & Reporting (Priority P3)

- [ ] T026 [Write] Write unit tests in `tests/unit/test_visualization.py` that verify plot‑generation functions run without error on synthetic data.  
  • Verify that `pytest tests/unit/test_visualization.py` passes.  

- [ ] T027 [US3] Implement `code/visualization.py` to create a PCoA plot (first two axes) colored by `depression_group`, add ellipses for group centroids, and save as `results/plots/pcoa_plot.png`.  
  • Verify that `pcoa_plot.png` exists, is a non‑empty PNG, and that the legend includes “High” and “Low”.  

- [ ] T028 [US3] Implement `code/visualization.py` to generate a heatmap of the top 20 taxa (by absolute correlation) with color intensity reflecting the correlation coefficient; save as `results/plots/taxa_heatmap.png`.  
  • Verify that `taxa_heatmap.png` exists and is non‑empty.  

- [ ] T029 [US3] Implement `code/report.py` to assemble `results/summary_report.txt`, which:  
  • Lists all significant associations (`q < 0.05`) with effect direction and magnitude,  
  • Summarizes the covariate‑delta check (T023a),  
  • Summarizes the KS‑test outcome (T024),  
  • Summarizes validation results if available (T023c).  
  • Verify that the report contains the headings “Significant Associations”, “Covariate Delta Check”, “KS‑Test Result”, and “Validation Summary” (when applicable).  

- [ ] T030 [US3] Verify that `results/plots/pcoa_plot.png`, `results/plots/taxa_heatmap.png`, and `results/summary_report.txt` exist and contain the expected content (basic sanity checks).  
  • Verify that each file exists, that PNGs are non‑empty, and that the summary report includes at least one significant association line.  

---

## Phase 6 – User Story 4: Validation on Independent Cohort (Priority P3)

- [ ] T030b [US4] Run a reference‑validator step that checks the accessibility of candidate independent cohorts (UK Biobank, MetaHIT, other Qiita studies) and writes `results/validation_urls_verified.json`.  
  • Verify that the JSON contains a boolean `cohort_available` flag for each candidate.  

- [ ] T031 [US4] Implement `code/validation.py`:  
  • If an independent cohort is verified, download it, compute correlations for the top significant taxa from `association_results.csv`, calculate the percentage of taxa whose effect direction matches the primary analysis, and write `data/processed/validation_results.csv` and `results/validation_report.txt`.  
  • If no cohort is accessible, write `results/validation_skip_report.md` indicating “SKIPPED” and mark SC‑003 as “Not Applicable”.  
  • Verify that when a cohort is available, `validation_results.csv` contains columns `taxon`, `primary_direction`, `validation_direction`, `match` and that `validation_report.txt` reports the match percentage.  

- [ ] T040 [US4] **SC‑003 Check** – After validation, compute the proportion of significant taxa with matching effect direction. If the proportion < 0.80, fail the pipeline with a clear error message; otherwise record a pass flag in `results/validation_report.txt`.  
  • Verify that the report contains “SC‑003 PASS” when ≥ 80 % match, otherwise the pipeline aborts.  

- [ ] T034 [US4] Ensure that, when validation runs, the results are saved to `data/processed/validation_results.csv` (or the skip report as above).  
  • Verify that the appropriate file exists based on cohort availability.  

---

## Phase 7 – Final Output & State Management

- [ ] T035 [P] Implement `code/state_manager.py` to compute SHA‑256 hashes of all final artifacts (CSV, PNG, JSON, MD files) and update `state/projects/PROJ-215-.../state.yaml` with `updated_at` and an `artifact_hashes` mapping.  
  • Verify that each final artifact’s hash in `state.yaml` matches a freshly computed hash.  

- [ ] T036 [P] Extend `code/report.py` to incorporate the timing metrics (see T037) and produce a consolidated `results/final_project_report.md` that enumerates:  
  • Data‑gap status,  
  • Retention statistics,  
  • All success‑criteria (SC‑001 – SC‑005) outcomes,  
  • Key visualizations,  
  • Validation outcome (if performed).  
  • Verify that the markdown file contains sections titled “Data Gap”, “Retention Statistics”, “Success Criteria”, “Visualizations”, and “Validation”.  

- [ ] T037a [P] Implement `code/timing.py` to record pipeline start and end timestamps, compute total runtime in seconds, and write `results/timing.json`.  
  • Verify that `timing.json` contains fields `start_time`, `end_time`, and `total_seconds` (positive integer).  

- [ ] T037 [P] Read `results/timing.json`, convert to hours, verify the runtime ≤ 4 hours, and write the result to `results/metrics.json` (field `total_runtime_hours`). If the runtime exceeds 4 hours, abort the pipeline with an error.  
  • Verify that `metrics.json` includes `total_runtime_hours` ≤ 4.0 and that the pipeline stops with an error if the limit is breached.  

- [ ] T042 [P] Validate the merged dataset against `specs/001‑investigating‑the‑relationship‑between‑g/contracts/dataset.schema.yaml`.  
  • Verify that `data/processed/cleaned_dataset.csv` conforms to the schema (all required columns present, types correct, no extra columns).  

- [ ] T043 [P] Validate the final association results against `specs/001‑investigating‑the‑relationship‑between‑g/contracts/output.schema.yaml`.  
  • Verify that `data/processed/association_results.csv` conforms to the schema (all required fields, correct types, no extra columns).  

---

### Dependency & Execution Order Summary  

| Phase | Must‑complete before | Key output files (used downstream) |
|-------|----------------------|------------------------------------|
| 0     | –                    | `results/feasibility_check.json`, `results/data_gap_report.md` |
| 1‑2   | Phase 0 (if data found) | `code/config.py`, `code/utils/logging.py`, `code/models.py`, `state/seeds.yaml`, `state.yaml` |
| 3     | Phases 1‑2           | `data/raw/merged_raw.parquet`, `data/interior/filtered_otu_table.biom`, `data/interior/median_depth.json`, `data/interior/estimated_loss.json`, `data/processed/preprocessed_otu_table.biom`, `data/processed/cleaned_dataset.csv` |
| 4     | Phase 3              | `data/processed/cleaned_dataset.csv`, `data/processed/alpha_metrics.csv`, `data/processed/bray_curtis.npz` |
| 5     | Phase 4              | `data/processed/association_results.csv` |
| 6     | Phase 4 (significant taxa) | `data/processed/association_results.csv`, `results/validation_urls_verified.json` |
| 7     | All previous phases  | All final CSV/JSON/PNG/MD artifacts |

All tasks now include explicit verification steps, proper ordering, contract validation, and enforcement of success criteria as required by the specification and the panel concerns.  
