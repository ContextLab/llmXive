# Tasks: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Inputs**: `spec.md`, `plan.md`, active contracts in `specs/001-the-effect-of-simulated-social-rejection/contracts/`, existing project skeleton (`code/config.py`, `code/utils/logger.py`, `code/data_model.py`, `code/ingest.py`, `code/preprocess.py`, `code/analyze.py`).

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US-1] Create the directory layout (`code/`, `code/utils/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/`) with placeholder `__init__.py` files; add `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, requests, pyarrow) and generate `quickstart.md` documenting installation via `pip install -r requirements.txt` and the single‑command pipeline invocation `python -m code.pipeline`.
  - Verification: `quickstart.md` exists and documents a runnable command; directory tree matches the plan.

- [ ] T002 [US-1] Implement `code/config.py` defining `PROJECT_ROOT`, `RAW_DIR`, `INTERIM_DIR`, `PROCESSED_DIR`, `RESULTS_DIR`, `PAPER_DIR`, `MAX_RAM_GB = 7`, `ALPHA_SET = {0.01, 0.05, 0.1}`, `SEED = 42`; add `code/utils/logger.py` recording timestamps, RAM usage, and key events to `data/processed/event_log.json`; define data‑model classes (`Dataset`, `PreprocessedRecord`, `AnalysisResult`) with a `design_type` attribute in `code/data_model.py`.
  - Verification: `python -c "from code import config"` succeeds; classes import without error.

### Data ingestion (both datasets)

- [ ] T003 [US-1] Download the verified OpenNeuro Cyberball dataset `ds000208.parquet` to `data/raw/ds000208.parquet` via streaming HTTP; abort with exit 1 if file size > 7 GB or fetch fails. Compute SHA‑256 checksum, write `data/raw/metadata_ds000208.json`, and create `data/raw/CITATION_ds000208.md` with the official citation (DOI [UNRESOLVED-CLAIM: 10.18112/openneuro.ds000208 — HTTP 404]). Add a `task` column with value `"cyberball"` to each record before validation.
  - Verification: `python -m code.ingest --dataset ds000208` exits 0; parquet exists; checksum matches; citation file present; `task` column added.

- [ ] T003b [US-1] Download the OpenNeuro reward‑feedback dataset `ds003392.parquet` (if publicly available) to `data/raw/ds003392.parquet` using the same streaming logic; abort with exit 1 if size > 7 GB or fetch fails. Compute SHA‑256, write `data/raw/metadata_ds003392.json`, and create `data/raw/CITATION_ds003392.md`. Add a `task` column with value `"reward"` to each record.
  - Verification: `python -m code.ingest --dataset ds003392` exits 0; files created; `task` column added.

- [ ] T004 [US-1] Validate `ds000208.parquet` against `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml`: check required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`), ensure both `rejection` and `control` appear, enforce value constraints, and confirm `task` column equals `"cyberball"`. On any failure, exit 1 with a clear error. Write `data/interim/ingest_validation_ds000208.json`.
  - Verification: Successful run produces a conforming validation report.

- [ ] T004b [US-1] Validate `ds003392.parquet` analogously (required columns plus `task` = `"reward"`). Write `data/interim/ingest_validation_ds003392.json`.
  - Verification: Validation passes or aborts with informative error.

- [ ] T005 [US-1] Run design determination logic (`process_overlap_and_design()`) using both validated datasets. Generate `data/interim/design_branch.json` containing `"design_type": "Between-Subjects"` (or `"Within-Subjects"` if full cross‑dataset ID matching succeeds) and a `"reason"` field explaining the decision. Also produce `data/interim/overlap_report.json` with counts of matching Participant IDs across the two datasets.
  - Verification: `design_branch.json` reflects the correct design type; `overlap_report.json` lists real overlap statistics.

### Preprocessing

- [ ] T006 [US-2] Load `data/raw/ds000208.parquet` (memory‑mapped) and `data/raw/ds003392.parquet`; drop duplicate rows and rows with missing `reaction_time` or `mood_rating`. For each `condition` group, invoke `_flag_outliers_iqr` (1.5 × IQR) to set `is_outlier`, then `_zscore_normalize` to create `rt_normalized` (per‑condition Z‑score). Write the combined preprocessed file to `data/interim/preprocessed_combined.csv`.
  - Verification: Script exits 0; output contains `is_outlier` and `rt_normalized` columns; memory usage ≤ 7 GB.

- [ ] T007 [US-2] Aggregate `preprocessed_combined.csv` per `participant_id` × `condition` into mean normalized RT (`rt_mean`) and mean mood (`mood_mean`), propagating `age`/`gender` where present. Write `data/processed/analysis_ready_combined.csv` (extended dataset schema). Simultaneously produce `data/interim/outlier_log.json` as a list of objects `{condition, iqr_lower, iqr_upper, flagged_count}` reflecting the actual IQR thresholds and counts.
  - Verification: Aggregated CSV has one row per participant‑condition; outlier log contains entries for all conditions with numeric thresholds and non‑zero counts where applicable.

## Phase 2: Complete the study and validate its evidence

- [ ] T008 [US-3] Load `data/processed/analysis_ready_combined.csv` and `data/interim/design_branch.json`. For each outcome (RT, mood) run a One‑Way ANOVA (`scipy.stats.f_oneway`) or ANCOVA with age/gender covariates if present. Perform Shapiro‑Wilk normality and Levene homogeneity checks; on failure apply (i) log‑transform RT, (ii) Welch’s ANOVA, (iii) Kruskal‑Wallis fallback, documenting the decision. Record convergence warnings and effect‑size confidence intervals for N < 30 per group. Write raw statistics to `results/analysis_raw.json`.
  - Verification: Script exits 0; raw JSON contains F, raw p, effect size, assumption diagnostics, and test‑selection notes.

- [ ] T009 [US-3] Apply Benjamini‑Hochberg FDR correction across all outcome p‑values; perform the α‑sensitivity sweep (α ∈ {0.01, 0.05, 0.1}) and record boolean significance flags. Write `results/analysis_output.json` conforming to `contracts/analysis_output.schema.yaml`.
  - Verification: JSON validates; `p_fdr ≥ p_raw` for every entry.

- [ ] T010 [US-3] Compute statistical power for each outcome at α = 0.01, 0.05, 0.1 using `statsmodels.stats.power.FTestAnovaPower` (medium effect size d = 0.5). Store per‑α power values in `results/power_by_alpha.json`.
  - Verification: File contains numeric `power_at_alpha` for each α.

- [ ] T011 [US-3] Consolidate `analysis_output.json`, `design_branch.json`, `outlier_sensitivity.json`, `power_by_alpha.json`, and phrasing‑check flags into `results/analysis_results.json` conforming to `contracts/analysis_results.schema.yaml`. Include `power_at_alpha` fields inside the `sensitivity_analysis` array.
  - Verification: JSON validates against the contract; all required fields present.

- [ ] T012 [US-3] Render `paper/report.md` from the validated results. Ensure:
  * Design type displayed as “Between‑Subjects”.
  * ANOVA (or fallback) tables show raw and FDR‑corrected p‑values.
  * Sensitivity table lists α values, significance booleans, and power numbers.
  * Limitations section contains the exact word **“associational”** and notes the absence of a verified reward‑feedback dataset.
  * Results section contains **no** occurrence of the word “causal”.
  * Explicit statement: “Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed.”
  Abort with non‑zero exit if any phrasing constraint fails.
  - Verification: Rendered markdown passes automated phrasing tests.

- [ ] T013 [US-3] After the full pipeline run, query the GitHub Actions run API (`GITHUB_RUN_ID`) to retrieve each step’s `duration_ms`, sum them, and write `results/runtime_report.json` with fields `total_seconds`, `peak_ram_gb`, and `runtime_ok` (true if total ≤ 21600 s and peak ≤ 7 GB). This satisfies SC‑002.
  - Verification: JSON reports summed duration matching GH step logs; `runtime_ok` is true.

- [ ] T014 [US-3] Run the Reference‑Validator Agent on all external citations (`data/raw/CITATION_*.md` and any literature citations referenced in `paper/report.md`). Abort with exit 1 if any citation fails verification, thereby satisfying Constitution II and FR‑009.
  - Verification: Validation succeeds; pipeline proceeds only when all citations are verified.

- [ ] T015 [US-3] **Design Determination (Alias for T005)** – Execute the same design‑type determination logic as T005 but expose the result as a standalone artifact `data/interim/design_type_summary.json` for downstream reporting. This satisfies the explicit plan‑level task T015 and ensures FR‑007/FR‑008 are directly addressed.
  - Verification: `design_type_summary.json` contains the design type and rationale; matches `design_branch.json`.

- [ ] T016 [US-3] Document the paper‑stage handoff in `paper/report.md` (section “Paper‑stage handoff”) listing the artifacts (`analysis_results.json`, `report.md`, `outlier_sensitivity.json`, `power_analysis.txt`, etc.) that the downstream paper pipeline will consume.
  - Verification: Hand‑off section present and accurately enumerates artifact paths.

- [ ] T017 [US-3] **Outlier‑Sensitivity Analysis** – Re‑run the ANOVA on the dataset with outliers retained versus outliers removed (as flagged in `outlier_log.json`). Record differences in effect sizes, p‑values, and confidence intervals; write `results/outlier_sensitivity.json` summarizing the impact.
  - Verification: JSON includes before/after statistics and indicates whether conclusions change.

- [ ] T018 [US-3] **A‑Priori Power Analysis (G*Power)** – Invoke G*Power (via its command‑line interface or a Python wrapper) to compute required sample size for a medium effect (Cohen’s d = 0.5) at α = 0.05, power = 0.80. Record the recommended N and the assumed parameters in `results/power_analysis.txt`.
  - Verification: Text file lists required N and matches G*Power output.

- [ ] T019 [US-3] **Unit and Integration Tests** – Add comprehensive tests in `tests/` covering:
  * Per‑condition IQR outlier flagging.
  * Z‑score normalization.
  * BH correction monotonicity (`p_fdr ≥ p_raw`).
  * α‑sensitivity coverage and power values.
  * Phrasing constraints on the rendered report.
  * End‑to‑end pipeline execution producing all result artifacts.
  Run with `pytest`; all must pass.
  - Verification: `pytest` returns 0; test suite covers every functional requirement.
