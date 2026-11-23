# Tasks: Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Input**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  

The list below groups related work into 15 substantive research tasks covering all functional requirements (FR‑001 – FR‑013) and user stories (US‑1 – US‑3). Checked boxes indicate completed, verified work; unchecked boxes denote work that must be (re)implemented or re‑validated.

## Phase 1 – Project scaffolding & core utilities  

- [ ] T001 [P] Create project root `projects/PROJ-298-statistical-analysis-of-publicly-availab/` with sub‑directories `code/`, `tests/`, `data/`, `notebooks/`, `state/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/`.  
  - Verify directory hierarchy exists and is writable.  

- [X] T002 [P] Add `code/requirements.txt` listing pinned versions of `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat`, `psutil`, `datasets`.  
  - Verify the file contains all expected packages (search for each name).  

- [ ] T003 [P] Implement `code/utils/hygiene.py` for SHA‑256 hashing of primary artifacts and automatic updates of `state/projects/PROJ-298‑statistical‑analysis‑of‑publicly‑availab.yaml`.  
  - Verify that after running the helper on a sample file the correct hash is recorded in the state YAML.  

- [ ] T004 [P] Implement `code/utils/contract_validation.py` to validate every JSON artifact against the schemas in `specs/001‑statistical‑analysis‑of‑publicly‑availab/contracts/`.  
  - Verify the validator passes on all existing JSON files.  

- [ ] T005 [P] Implement `code/viz/templates.py` that injects the mandatory disclaimer  
  > “Limitation: All findings are associational and do not imply causality.”  
  into every generated report, figure, or notebook output.  
  - Verify a sample PNG and a generated HTML report contain the footer text.  

## Phase 2 – Data acquisition  

- [ ] T006 [P] Download the Stack Overflow “Tech Stack” taxonomy from the verified HuggingFace dataset and write `data/taxonomy/survey_2023.json`.  
  - Verify file exists, checksum matches the published SHA‑256, and JSON is well‑formed.  

- [ ] T007 [P] Download the reference calendar of releases/conferences (`data/events/reference_calendar.json`) from the verified source listed in the plan.  
  - Verify file existence, checksum, and schema compliance.  

- [ ] T008 [P] Download the `PostsTags` table (canonical URL `[UNRESOLVED-CLAIM: https://archive.org/download/stackexchange/stackoverflow.com-PostsTags.parquet` — HTTP 404]) and store it as `data/raw/PostsTags.parquet`.  
  - Verify the parquet file is readable, contains the expected columns, and matches the schema defined in the spec.  

## Phase 3 – Pre‑processing  

- [ ] T009 [P] Implement `code/data/preprocess.py` to:   <!-- FAILED-IN-EXECUTION: code/data/preprocess.py exit=1 -->
  - normalize tag strings (lower‑case, trim),  
  - aggregate monthly counts for the period 2015‑01‑01 → 2023‑12‑01,  
  - filter out tags with < 12 months of data,  
  - select the top 50 tags by total frequency,  
  - write `data/processed/monthly_tag_counts.parquet`, `data/processed/top_50_tags.json`, and `data/processed/data_sufficiency_report.json`.  
  - Verify each output file conforms to its respective schema (`dataset.schema.yaml`, custom top‑50 schema).  

## Phase 4 – External metric collection & tag‑to‑repo mapping  

- [ ] T010 [P] Implement `code/data/external.py` to fetch, cache, and store for each of the top 50 tags:  
  - total GitHub stars (via GitHub Search API, topic query) and  
  - NPM download counts (via NPM Registry API, keyword query).  
  - Write `data/processed/external_metrics.json`; log unmapped tags to `data/processed/unmapped_tags.log` and API errors to `data/processed/external_fetch_errors.log`.  
  - Verify `external_metrics.json` matches the `external_metrics.schema.yaml` and that both log files are present.  

- [ ] T010a [P] Compute Pearson correlation between each tag’s trend slope (from T012) and its external metric (GitHub stars or NPM downloads).  
  - Write `data/processed/correlation_results.json` containing `tag`, `slope`, `external_metric`, `pearson_r`, and interpreted strength (`Strong`/`Moderate`/`Weak`).  
  - Verify the JSON conforms to `correlation_results.schema.yaml`.  

- [ ] T011 [P] Implement `code/analysis/mapping.py` to read `data/processed/external_metrics.json` and produce a definitive mapping file `data/processed/tag_mappings.json`.  
  - Must adhere to the mapping schema, create `unmapped_tags.log` for any tag without a successful repository match, and record the mapping provenance.  
  - **Verification**: Run the script; confirm `tag_mappings.json` exists, validates against its schema, and that the log file records any failures.  

## Phase 5 – Trend detection, power analysis, and result aggregation  

- [ ] T012 [P] Implement `code/analysis/trends.py` to run the Modified Mann‑Kendall test with pre‑whitening on each of the top 50 monthly time series and compute Theil‑Sen slopes and post‑hoc power analysis.  
  - Write intermediate results to `data/processed/trend_intermediate.json` (including `p_value`, `power`, `mdes`).  
  - Verify required fields are present and schema‑compliant.  

- [ ] T012a [P] From the intermediate results, bootstrap (1 000 block‑bootstrap iterations) 95 % confidence intervals for each slope and write `data/processed/confidence_interval.json`.  
  - Validate against `confidence_interval.schema.yaml`.  

- [ ] T013 [P] Aggregate trend‑related outputs into the final artifact `data/processed/trend_results.json`, including:  
  - `trend_slope`, `p_value`, `classification`, `power`, `mdes`, `confidence_interval_lower`, `confidence_interval_upper`, and the Pearson‑r correlation from `correlation_results.json`.  
  - Verify the file validates against `specs/001‑statistical‑analysis‑of‑publicly‑availab/contracts/trend_results.schema.yaml`.  

## Phase 6 – Time‑series decomposition & seasonal validation  

- [ ] T014 [P] Implement `code/analysis/decomposition.py` to:  
  - run Augmented Dickey‑Fuller (ADF) test on each series, apply first‑order differencing when non‑stationary,  
  - conduct a seasonality pre‑test (spectral analysis p < 0.05 or autocorrelation at lag 12 > 0.3) and flag each tag in `data/processed/seasonality_flags.json`,  
  - apply STL decomposition for seasonal series or Hodrick‑Prescott filter for non‑seasonal series,  
  - perform Ljung‑Box test (lag = 12) on residuals and a Rayleigh test against `data/events/reference_calendar.json`, storing results in `data/processed/decomposition_validation.json`,  
  - output component JSON (`observed`, `trend`, `seasonal` (if any), `residual`) to `data/processed/decomposition_components.json`,  
  - generate multi‑panel PNG plots `figures/decomposition_{tag}.png` with the limitation footer.  
  - Verify all JSON artifacts conform to their schemas and that each PNG contains the disclaimer.  

## Phase 7 – Co‑occurrence clustering & alignment  

- [ ] T015 [P] Implement `code/analysis/clustering.py` to:  
  - compute the Jaccard similarity matrix for all tag pairs among the top 50, write `data/processed/jaccard_matrix.json`;  
  - perform hierarchical clustering, run a 1 000‑iteration permutation test to compare intra‑ vs. inter‑cluster similarity, write `data/processed/cluster_results.json`;  
  - calculate the Cluster Label Alignment Score against `data/taxonomy/survey_2023.json` using fuzzy matching (Levenshtein ≤ 2), write `data/processed/cluster_alignment.json` and log warnings to `data/processed/clustering_warnings.log` if the score < 0.8;  
  - generate dendrogram PNGs `figures/cluster_{tag}.png` with the limitation footer.  
  - Verify JSON files match their schemas, alignment score ≥ 0.8 (or warning logged), and PNGs contain the disclaimer.  

## Phase 8 – Orchestration, reproducibility, and final verification  

- [ ] T016 [P] Implement deterministic seeding module `code/utils/seeding.py` exposing `set_global_seed(seed)` and invoke it at the start of every stochastic script.  
  - Verify two consecutive runs with the same seed produce identical outputs (hash comparison).  

- [ ] T017 [P] Implement orchestrator `code/main.py` that runs the full pipeline in strict order:  
  `T008 → T009 → T016 → T010 → T010a → T011 → T012 → T012a → T013 → T014 → T015 → T018 → T019 → T020`.  
  The script aborts immediately on any failure (exit ≠ 0).  
  - Verify that injecting a failure in an early step causes a non‑zero exit status.  

- [ ] T018 [P] Update `quickstart.md` with the command `python code/main.py`, an estimated runtime ≤ 6 h, and a note that the runner is CPU‑only. Also add a verification step that reads `execution_time_seconds` from the state YAML and asserts it does not exceed the documented estimate.  
  - Verify the markdown contains the exact command line, the runtime estimate, the CPU‑only resource statement, and the new verification step.  

- [ ] T019 [P] Global limitation‑footer audit: scan all generated reports, figures, and notebooks to confirm the mandatory disclaimer appears in every artifact.  
  - Fail the run if any file lacks the footer.  

- [ ] T020 [P] End‑to‑end verification task:  
  - Validate schema compliance for **all** JSON outputs (`trend_results.json`, `confidence_interval.json`, `correlation_results.json`, `decomposition_components.json`, `cluster_results.json`, etc.).  
  - Confirm existence of every expected file listed in the plan.  
  - Record total execution time in `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` under `execution_time_seconds`.  
  - Assert `execution_time_seconds ≤ 21600` (6 h).  
  - Verify that the runtime recorded matches the estimate documented in `quickstart.md`.  
  - **Verification**: Run the verifier script; ensure it reports “PASS” for all checks.  

## Phase 9 – Notebook generation & manual verification  

- [ ] T021 [P] Generate reproducible Jupyter notebooks for each major analysis stage (data ingestion, trend analysis, decomposition, clustering).  
  - Notebooks must import code from `code/`, execute end‑to‑end, and save all figures and tables to the appropriate `figures/` and `data/processed/` directories.  
  - Validate notebooks run without errors on a fresh runner and that they contain the limitation footer in all output cells.  

- [ ] T022 [P] Implement a manual verification script `code/verification/verify_correlation.py` that recalculates Pearson‑r for a random sample of tags and asserts the absolute difference from `correlation_results.json` is < 1e‑6.  
  - Include this script in the end‑to‑end verification (T020) and ensure it passes.  
