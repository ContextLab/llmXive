# Tasks: Statistical Analysis of Publicly Available Stack Overflow Question Tags

**Input**: Design documents from `/specs/001-stat-so-tag-trends/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

## Phase 1 – Project Setup & Core Utilities  

- [ ] T001 [P] Create project root `projects/PROJ-298-statistical-analysis-of-publicly-availab/` and sub‑directories (`code/`, `tests/`, `data/`, `notebooks/`, `state/`, `data/raw/`, `data/processed/`, `data/events/`, `data/taxonomy/`).  
- [ ] T002 Create `requirements.txt` in `code/` listing `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `nbformat`, `psutil`, `datasets`.  
- [ ] T002V Verify `requirements.txt` exists and contains the expected package list.  
- [ ] T003 Configure linting/formatting (flake8 + black) for the repository.  
- [ ] T003V Run flake8 and black; fail on any violations.  
- [ ] T004 Implement `code/utils/hygiene.py` – SHA‑256 hashing and state‑file updates (FR‑012).  
- [ ] T004V Verify SHA‑256 hashes are computed for all primary artifacts and recorded in the state YAML.  
- [ ] T005 Implement `code/utils/contract_validation.py` – schema enforcement for all `contracts/` files (Constitution Principle V).  
- [ ] T005V Run contract validator on every file in `contracts/` and assert success.  
- [ ] T006 Implement `code/viz/templates.py` – inject mandatory limitation header/footer into all generated reports/figures (FR‑011).  
- [ ] T006V Sample a generated report/figure and confirm the limitation footer is present.  
- [ ] T007 Verify that the directory hierarchy created by T001 exists; fail loudly if any required folder is missing.  

## Phase 2 – Data Acquisition & Pre‑processing  

- [ ] T008 Download the taxonomy of Stack Overflow “Tech Stack” from the verified HuggingFace dataset and write `data/taxonomy/survey_2023.json`.  
- [ ] T008V Verify `survey_2023.json` exists, matches expected checksum, and conforms to its schema.  
- [ ] T009 Download the reference calendar of releases/conferences (verified source) and write `data/events/reference_calendar.json`.  
- [ ] T009V Validate `reference_calendar.json` against its schema and checksum.  
- [ ] T010 Download the `PostsTags` table (canonical URL `[UNRESOLVED-CLAIM: https://archive.org/.../PostsTags.parquet` — HTTP 404] with fallback to HuggingFace) and store it as `data/raw/PostsTags.parquet`.  
- [ ] T010V Confirm `PostsTags.parquet` download succeeded, is readable, and matches the expected schema.  
- [ ] T011 Implement `code/data/preprocess.py` to:  
  - normalize tag strings (lowercase, trim),  
  - aggregate monthly counts for 2015‑2023,  
  - filter out tags with < 12 months of data,  
  - select the top 50 tags by total frequency,  
  - output `data/processed/monthly_tag_counts.parquet`, `data/processed/top_50_tags.json`, and `data/processed/data_sufficiency_report.json`.  
- [ ] T011V Validate the three processed files against `contracts/dataset.schema.yaml` and related schemas.

## Phase 3 – External Validation Metrics  

- [ ] T012 Implement `code/data/external.py` to fetch, cache, and store GitHub star counts and NPM download numbers for each tag in `data/processed/top_50_tags.json`.  
  - Write raw metrics to `data/processed/external_metrics.json`.  
  - Log unmapped tags to `data/processed/unmapped_tags.log` and API errors to `data/processed/external_fetch_errors.log`.  
- [ ] T012V Verify `external_metrics.json` conforms to `contracts/external_metrics.schema.yaml` and that both log files are generated.

## Phase 4 – Tag‑to‑Repository Mapping  

- [ ] T013 [US1] Implement `code/analysis/mapping.py` to read `external_metrics.json` and produce a definitive mapping file `data/processed/tag_mappings.json`.  
  - Must respect the schema in `contracts/external_metrics.schema.yaml`.  
  - Must create `unmapped_tags.log` for any tag without a successful match.  

## Phase 5 – Trend Detection & Power Analysis  

- [ ] T014 [US1] Implement `code/analysis/trends.py` to run the Modified Mann‑Kendall test with pre‑whitening, compute Theil‑Sen slopes, and classify each tag (Growth / Decline / Stable / Insufficient Data).  
  - Output intermediate results to `data/processed/trend_intermediate.json`.  
- [ ] T014V Validate that `trend_intermediate.json` exists and conforms to its intermediate results schema (ensuring required fields are present).  
- [ ] T015 [US1] Extend `trends.py` to perform **post‑hoc power analysis** and **Minimum Detectable Effect Size (MDES)** via Monte‑Carlo simulation; augment `trend_intermediate.json` with `power` and `mdes` fields.  
- [ ] T015V Validate that `trend_intermediate.json` now includes `power` (0 ≤ power ≤ 1, ≥0.8 for significant trends) and `mdes` (>0) fields and that the values are within plausible ranges.  
- [ ] T017 [US1] Implement block‑bootstrap (12‑month blocks, **1000 iterations**) in `code/analysis/trends.py` to compute 95 % confidence intervals for Theil‑Sen slopes; write `data/processed/confidence_interval.json`.  
- [ ] T017V Ensure `confidence_interval.json` contains both `lower` and `upper` bounds, conforms to its schema, and was generated with 1000 iterations.  
- [ ] T018 [US1] Implement `code/analysis/correlation.py` to correlate trend slopes with the external metrics (GitHub/NPM) using Pearson’s r, **interpret magnitude** (Strong ≥ 0.7, Moderate 0.3‑0.7, Weak < 0.3), and write `data/processed/correlation_results.json`.  
- [ ] T018V Verify `correlation_results.json` schema, presence of the magnitude interpretation field, and that numeric values match a manual verification script (error < 1e‑6).  
- [ ] T019 [US1] Create reproducible notebook `notebooks/02_trend_analysis.ipynb` that runs the full US‑1 pipeline, produces the required tables/figures, and uses `templates.py` to add the limitation footer.  
- [ ] T019V Execute the notebook end‑to‑end, confirm successful run, and verify the limitation footer is injected in all generated artifacts.  
- [ ] T016 [US1] Aggregate all trend information (slopes, p‑values, classification, power, MDES, confidence intervals from T017) into the final artifact `data/processed/trend_results.json`.  
- [ ] T016V Validate `trend_results.json` against `contracts/trend_results.schema.yaml`, ensuring all required fields are present and correctly typed.  

## Phase 6 – Time‑Series Decomposition & Seasonality  

- [ ] T020 [US2] Implement seasonality pre‑test (`code/analysis/decomposition.py`) using spectral analysis (p < 0.05) or autocorrelation at lag 12 (> 0.3); output `data/processed/seasonality_flags.json`.  
- [ ] T020V Verify `seasonality_flags.json` exists and conforms to its schema.  
- [ ] T021 [US2] Implement Augmented Dickey‑Fuller test for each tag; decide on first‑order differencing; write `data/processed/adf_results.json`.  
- [ ] T021V Validate `adf_results.json` schema and that ADF statistics are correctly recorded.  
- [ ] T022 [US2] Based on seasonality flags, apply STL (seasonal) or Hodrick‑Prescott (non‑seasonal) to the (differenced) series; store components in `data/processed/decomposition_components.json`.  
- [ ] T022V Ensure decomposition components conform to their schema and that the method used matches the seasonality flag for each tag.  
- [ ] T023 [US2] Perform Ljung‑Box test (lag = 12) on residuals and Rayleigh test against `reference_calendar.json`; write results to `data/processed/decomposition_validation.json`.  
- [ ] T023V Verify that Ljung‑Box and Rayleigh test results are present, valid, and schema‑compliant.  
- [ ] T024 [US2] Generate multi‑panel plots (Observed, Trend, Seasonal, Residual) for each analysed tag, saving PNGs under `figures/decomposition_{tag}.png` and injecting the limitation header/footer.  
- [ ] T024V Scan generated PNGs to confirm each includes the mandatory limitation footer.  
- [ ] T025 [US2] Create notebook `notebooks/03_decomposition.ipynb` demonstrating the full decomposition workflow for a representative tag (e.g., “react”).  
- [ ] T025V Run the notebook end‑to‑end, verify successful execution, and confirm all expected plots are produced with the footer.  

## Phase 7 – Co‑occurrence Clustering  

- [ ] T026 [US3] Compute the Jaccard similarity matrix for all pairs of the top 50 tags (using post‑tag co‑occurrence); write `data/processed/jaccard_matrix.json`.  
- [ ] T026V Validate `jaccard_matrix.json` existence and schema compliance.  
- [ ] T027 [US3] Perform hierarchical clustering on the Jaccard matrix and run a 1000‑iteration permutation test to assess intra‑ vs. inter‑cluster similarity; output `data/processed/clustering_results.json`.  
- [ ] T027V Verify `clustering_results.json` schema, that the permutation test was executed, and that statistical significance is recorded.  
- [ ] T028 [US3] Calculate the Cluster Label Alignment Score against `survey_2023.json` using fuzzy matching (Levenshtein ≤ 2); write `data/processed/cluster_alignment.json` and log warnings to `data/processed/clustering_warnings.log` if the score falls below 0.8.  
- [ ] T028V Ensure the alignment score ≥ 0.8; if below, confirm a warning is logged.  
- [ ] T029 [US3] Produce dendrogram and cluster visualizations saved as `figures/cluster_{tag}.png`.  
- [ ] T029V Verify each dendrogram PNG contains the limitation footer.  
- [ ] T030 [US3] Create notebook `notebooks/04_clustering.ipynb` that walks through similarity computation, clustering, permutation testing, and alignment scoring.  
- [ ] T030V Execute the notebook and confirm it runs without error.  
- [ ] T031 [US3] Aggregate final clustering artefacts into `data/processed/cluster_results.json`.  
- [ ] T031V Validate `cluster_results.json` schema, completeness, and that all required fields are present.  

## Phase 8 – Reproducibility, Orchestration & Final Verification  

- [ ] T032 [P] Implement deterministic seeding module `code/utils/seeding.py` exposing `set_global_seed(seed)`; invoke it at the start of the pipeline (covers all stochastic steps).  
- [ ] T032V Run a reproducibility check confirming that seeded runs produce identical outputs.  
- [ ] T033 [P] Implement orchestration script `code/main.py` that sequentially runs the pipeline steps in the correct order:  
  T010 → T011 → T012 → T013 → T014 → T014V → T015 → T015V → T017 → T017V → T018 → T018V → T019 → T019V → T016 → T016V → T020 → T020V → T021 → T021V → T022 → T022V → T023 → T023V → T024 → T024V → T025 → T025V → T026 → T026V → T027 → T027V → T028 → T028V → T029 → T029V → T030 → T030V → T031 → T031V → T032 → T033V.  
  The script must abort immediately on any upstream failure (“Fail loudly”).  
- [ ] T033V Simulate a failure in an early step and verify the script exits with a non‑zero status.  
- [ ] T034 [P] Update `quickstart.md` to describe execution via `python code/main.py`, list expected runtime (≤ 6 h), and note CPU‑only resource limits.  
- [ ] T034V Parse `quickstart.md` and assert it contains the correct command, runtime estimate, and resource limit statements.  
- [ ] T035 [P] Verify that every generated report, figure, and notebook contains the mandatory limitation footer (“Limitation: All findings are associational and do not imply causality.”). Fail the run if any file is missing the disclaimer.  
- [ ] T035V Perform a global scan of all output artifacts to confirm the footer is present everywhere.  
- [ ] T036 [P] Run end‑to‑end verification:  
  - schema validation for all JSON outputs (`trend_results`, `confidence_interval`, `correlation_results`, `decomposition_components`, `cluster_results`, etc.),  
  - confirm existence of all expected files,  
  - record total execution time in `state/projects/PROJ-298-statistical-analysis-of-publicly-availab.yaml` under `execution_time_seconds`,  
  - assert `execution_time_seconds ≤ 21600` (6 h).  
- [ ] T036V Independently validate schema compliance, file existence, and the ≤ 6 h constraint without assuming prior task success.

---

### Dependency Mapping (selected)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑002 | T010, T011 |
| FR‑003, FR‑013 | T014, T015, T016 |
| FR‑004, FR‑009 | T020‑T024 |
| FR‑005, FR‑008 | T026‑T030 |
| FR‑007 | T012, T018 |
| FR‑010 | T017 |
| FR‑011 | T006, T024, T035 |
| FR‑012 | T004, T004V |
| US‑1 | T013‑T019 |
| US‑2 | T020‑T025 |
| US‑3 | T026‑T031 |

---

**Checkpoint Summary**

- Core infrastructure (T001‑T007) now includes verification and correct parallel tagging.  
- Data ingestion, preprocessing, and external metric collection are verified (T008‑T012 and their V‑tasks).  
- Mapping (T013) and trend aggregation (T016) are correctly ordered and fully verified.  
- Decomposition and clustering pipelines include exhaustive verification.  
- Orchestrator (T033) respects proper execution order and abort behavior.  
- All spec‑mandated success criteria now have corresponding verification tasks, including SC‑006 and FR‑007 interpretation.  
- Missing verification task T035V added.  