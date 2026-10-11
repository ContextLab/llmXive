# Tasks: The Effect of Simulated Social Rejection on Behavioral Responses

**Inputs**: `spec.md`, `plan.md`, existing project skeleton.  
**Goal**: End‑to‑end pipeline that (1) downloads and validates the OpenNeuro ds000208 (rejection) and ds003392 (reward) datasets, (2) preprocesses behavioral logs, (3) runs the appropriate statistical test (within‑ or between‑subjects) based on cross‑dataset ID matching, (4) applies FDR correction and a sensitivity sweep, and (5) produces a reproducible report that respects all functional requirements (FR‑000 – FR‑008) and success criteria (SC‑001 – SC‑004).

---

## Phase 1 – Project scaffolding & quickstart (US0)

- [X] **T001** [ ] [US0] Create the directory layout (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`, `reports/`) and placeholder `__init__.py` files; add `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, requests) and generate `quickstart.md` that documents (a) installation via `pip install -r requirements.txt` and (b) the single‑command pipeline invocation `python -m code.pipeline`.

---

## Phase 2 – Core infrastructure (US0)

- [X] **T002** [ ] [US0] Implement `code/config.py` defining:
  - `PROJECT_ROOT`, `RAW_DIR`, `INTERIM_DIR`, `PROCESSED_DIR`, `REPORTS_DIR`
  - `MAX_RAM_GB = 7`
  - `ALPHA_SET = {0.01, 0.05, 0.1}`
  - a fixed random seed (`SEED = 42`)
- Add a minimal logger in `code/utils/logger.py` that records timestamps, RAM usage, and key events to `data/processed/event_log.json`.
- Define data‑model classes (`Dataset`, `PreprocessedRecord`, `AnalysisResult`) with a `design_type` attribute in `code/data_model.py`.

---

## Phase 3 – User Story 1: Data ingestion & design determination (US1)

- [ ] **T003** [ ] [US1] In `code/ingest.py`:
  1. Query the OpenNeuro API for ds000208 (rejection) and ds003392 (reward), sum file sizes for each, and **halt with exit‑code 1** if either estimate > 7 GB.
  2. Stream‑download both datasets into `data/raw/` preserving their original filenames.
  3. Write `data/raw/dataset_manifest.json` containing an array of `{url, sha256: null, size_bytes, file_count, dataset_id}` entries.

- [ ] **T004** [ ] [US1] Still in `code/ingest.py`: <!-- FAILED-IN-EXECUTION: code/ingest.py exit=1 -->
  1. Load the primary CSV from each dataset, verify presence of columns `participant_id`, `condition`, `reaction_time`, `mood_rating`; on failure **exit 1** with an error message.
  2. Confirm that both `Rejection` and `Control` conditions appear in the rejection dataset and that the reward dataset contains the required reward‑feedback variables; produce `data/interim/condition_report.json` (`{rejection_present: bool, control_present: bool, reward_present: bool}`).

- [ ] **T005** [ ] [US1] In `code/ingest.py`:
  1. Compute the set of participant IDs for each condition in the rejection dataset and the set of IDs present in the reward dataset; write `data/interim/overlap_report.json` (`{overlap: bool, rejection_ids: [...], reward_ids: [...]}`).
  2. Based on the overlap report, decide the experimental design:
     - If `overlap` is true → `design_type="Within-Subjects"`.
     - Else → `design_type="Between-Subjects"`.
  3. Emit `data/interim/design_branch.json` (`{design_type, reason}`) and append the decision to `data/processed/metadata.json`.

- [ ] **T006** [ ] [US1] Finalize ingestion:
  1. Compute the SHA‑256 hash of each downloaded raw file and update `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml` under `artifact_hashes.<dataset_id>.sha256` and `size_bytes`; also set `updated_at` to the current ISO timestamp.
  2. Create `data/raw/CITATION.md` that cites both OpenNeuro datasets (DOI 10.18112/openneuro.ds000208.v1.0.0 and DOI 10.18112/openneuro.ds003392.v1.0.0) and records the access date.

---

## Phase 4 – User Story 2: Preprocessing & feature extraction (US2)

- [ ] **T007** [ ] [US2] In `code/preprocess.py`: <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  1. Load each raw CSV, drop duplicate rows, and drop rows with missing `reaction_time` or `mood_rating`.
  2. Save the cleaned tables to `data/interim/cleaned_<dataset_id>.csv`.

- [ ] **T008** [ ] [US2] Still in `code/preprocess.py`:
  1. Within each `condition` group of each dataset, compute the IQR of `reaction_time`; flag rows where `reaction_time` lies outside `1.5 × IQR` and add a boolean column `is_outlier`.
  2. Z‑score normalize `reaction_time` per condition and overwrite the column with the normalized values.
  3. Write the resulting datasets to `data/interim/preprocessed_<dataset_id>.csv`.

- [ ] **T009** [ ] [US2] Still in `code/preprocess.py`:
  1. For the rejection dataset, aggregate `preprocessed_ds000208.csv` to obtain, for every `participant_id` × `condition`, the mean normalized reaction time (`mean_rt`) and the mean mood rating (`avg_mood`).
  2. Persist these features to `data/processed/features_ds000208.csv`.
  3. Produce an outlier audit trail `data/interim/outlier_log.json` that records, for each condition, the IQR thresholds used and the count of flagged rows.

---

## Phase 5 – User Story 3: Statistical analysis, FDR, sensitivity & reporting (US3)

- [ ] **T010** [ ] [US3] In `code/analysis.py`: <!-- FAILED-IN-EXECUTION: code/analyze.py exit=1 -->
  1. Read the appropriate feature file (`features_ds000208.csv`) and the `design_type` from `data/processed/metadata.json`.
  2. If `Within-Subjects`, run a repeated‑measures ANOVA via `statsmodels.stats.anova.AnovaRM`; if `Between-Subjects`, run a one‑way ANOVA via `scipy.stats.f_oneway`.
  3. Store raw statistics (`F`, `p_raw`, effect sizes) in `data/processed/analysis_raw.json`.

- [ ] **T011** [ ] [US3] Still in `code/analysis.py`:
  1. Apply the Benjamini‑Hochberg procedure to all `p_raw` values, creating a new column `p_fdr`.
  2. Perform a sensitivity sweep over α ∈ {0.01, 0.05, 0.1}; for each α record whether each test is significant. Save results to `data/processed/sensitivity.json`.
  3. Write the combined output (`analysis_fdr.json` plus `sensitivity.json`) to `data/processed/`.

- [ ] **T012** [ ] [US3] In `code/report.py`:
  1. Assemble a Markdown report `reports/final_report.md` that includes:
     - A results table with raw and FDR‑corrected p‑values.
     - The sensitivity table covering all three α levels.
     - A **Limitations** section that contains the exact phrase “associational”.
     - A **Results** section that **does not** contain the word “causal”.
  2. Verify the phrasing constraints programmatically; abort with a non‑zero exit code if violated.

- [ ] **T013** [ ] [US3] In `code/report.py`:
  1. Write the definitive JSON results file `data/processed/final_results.json` containing:
     - `design_type`
     - All statistics from `analysis_fdr.json`
     - The `p_fdr` column
  2. Run two verification scripts (in `tests/`):
     - `tests/verify_fdr.py` asserts `p_fdr ≤ p_raw` for every row and writes `tests/results/fdr_verification.json`.
     - `tests/verify_sensitivity.py` asserts that the sensitivity report includes entries for α = 0.01, 0.05, 0.1 and writes `tests/results/alpha_coverage.json`.

- [ ] **T019** [ ] [US3] In `tests/verify_fdr.py` (or a new helper):
  1. After verification, generate a concise artifact `data/processed/p_fdr_verification.json` summarizing the pass/fail status for the SC‑003 requirement.

---

## Phase 6 – Polishing, CI & benchmarking (US4)

- [ ] **T015** [ ] [US4] Implement `code/benchmark.py` that, when invoked on the full pipeline, records wall‑clock start/end times, peak memory usage, and CPU utilization; output these metrics to `data/processed/ci_runtime_total.json`. The script also writes a boolean `runtime_ok` flag indicating the total time ≤ 6 hours.

- [ ] **T014** [ ] [US4] Add a GitHub Actions workflow `.github/workflows/ci.yml` that:
  1. Spins up the `ubuntu‑latest` free‑tier runner.
  2. Enforces a maximum runtime of **6 hours** and a RAM ceiling of **7 GB** (via `ulimit` and `timeout` wrappers).
  3. Executes the full pipeline (`python -m code.pipeline`).
  4. After the run, reads `data/processed/ci_runtime_total.json` and fails the job if `runtime_ok` is false.

- [ ] **T020** [ ] [US4] Add a lightweight verification task `code/ci_verify_runtime.py` that reads `ci_runtime_total.json` and writes `data/processed/ci_runtime_verification.json` with explicit fields `total_seconds`, `peak_ram_gb`, and `pass` for SC‑002 auditability.
