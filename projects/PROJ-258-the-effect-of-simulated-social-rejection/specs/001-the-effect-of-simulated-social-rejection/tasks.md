# Tasks: The Effect of Simulated Social Rejection on Behavioral Proxies (Reaction Time and Mood)

**Inputs**: `spec.md`, `plan.md`, active contracts in `specs/001-the-effect-of-simulated-social-rejection/contracts/`, existing project skeleton (`code/config.py`, `code/utils/logger.py`, `code/data_model.py`).
**Goal**: End-to-end CPU-only pipeline that (1) downloads and validates the verified OpenNeuro ds000208 Cyberball parquet, (2) preprocesses behavioral logs (per-condition IQR outliers, Z-scored RT, per-participant aggregation), (3) runs a Between-Subjects One-Way ANOVA (or ANCOVA / Welch / Kruskal-Wallis fallback) on RT and mood, (4) applies Benjamini-Hochberg FDR correction and an α-sensitivity sweep, and (5) produces a reproducible report satisfying FR-000–FR-009 and SC-001–SC-004.

**Revision note**: The prior task list tasked downloading a second dataset (ds003392) for which no verified open source exists, and tasked writing platform-owned `state/...` and `.github/` paths — both contradict the active plan and platform rules. Those instructions are corrected here: the study uses ds000208 only with a Between-Subjects design (per plan.md and FR-007), and all outputs go under `data/`, `results/`, `paper/`, `code/`, `tests/`. Verified scaffolding tasks T001–T002 are preserved as complete.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Create the directory layout (`code/`, `code/utils/`, `data/raw/`, `data/interim/`, `data/processed/`, `results/`, `paper/`, `tests/`) with placeholder `__init__.py` files; add `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, requests, pyarrow) and generate `quickstart.md` documenting installation via `pip install -r requirements.txt` and the single-command pipeline invocation `python -m code.pipeline`.
  - Verification: `quickstart.md` exists and documents a runnable command; directory tree matches the plan.

- [ ] T002 [US1] Implement `code/config.py` defining `PROJECT_ROOT`, `RAW_DIR`, `INTERIM_DIR`, `PROCESSED_DIR`, `RESULTS_DIR`, `PAPER_DIR`, `MAX_RAM_GB = 7`, `ALPHA_SET = {0.01, 0.05, 0.1}`, `SEED = 42`; add `code/utils/logger.py` recording timestamps, RAM usage, and key events to `data/processed/event_log.json`; define data-model classes (`Dataset`, `PreprocessedRecord`, `AnalysisResult`) with a `design_type` attribute in `code/data_model.py`.
  - Verification: `python -c "from code import config"` succeeds; classes import without error.

- [ ] T003 [US1] In `code/ingest.py`, download the verified OpenNeuro ds000208 parquet (the exact URL recorded in `specs/001-the-effect-of-simulated-social-rejection/research.md`) into `data/raw/ds000208.parquet` via a streaming HTTP download; before download, query the file size and **halt with exit code 1** if the size exceeds 7 GB (FR-001). The loader must FAIL LOUDLY on any fetch error — no synthetic/mock fallback. Compute the SHA-256 checksum and write `data/raw/metadata.json` (`{dataset_id, checksum_sha256, download_timestamp, citation}`) plus a human-readable `data/raw/CITATION.md` with the official OpenNeuro citation (DOI 10.18112/openneuro.ds000208) and access date (Constitution III).
  - Verification: `data/raw/ds000208.parquet` exists, is non-empty, `metadata.json` checksum matches a recomputed SHA-256, and `CITATION.md` cites the dataset.

- [ ] T004 [US1] Still in `code/ingest.py`, validate the raw parquet against `contracts/dataset.schema.yaml` and `contracts/ingest_schema.schema.yaml`: verify presence of required columns (`participant_id`, `condition`, `reaction_time`, `mood_rating`), verify both `rejection` and `control` values appear in `condition`, and verify value constraints (RT ≥ 0; mood within the documented scale). On any missing variable, **exit 1** with a clear error (FR-000, FR-001, SC-001). Write `data/interim/ingest_validation_report.json` containing required-column presence, data types, constraints, and `single_cohort_validation` (`is_single_cohort`, `conditions_present`).
  - Verification: script exits 0 with all checks passing; the validation report conforms to the ingest schema.

- [ ] T005 [US1] In `code/ingest.py`, implement design determination (FR-007, FR-008): since only ds000208 exists (no verified open reward-feedback dataset — do NOT attempt to download ds003392 or fabricate reward data), write `data/interim/design_branch.json` with `{"design_type": "Between-Subjects", "reason": "single-cohort Cyberball dataset; no verified open reward-feedback dataset available"}` and append the decision to `data/processed/metadata.json`. If participant IDs happen to match across conditions within the cohort, note the matching and the limitation that a Within-Subjects modulation test is not performed.
  - Verification: `design_branch.json` contains `"design_type": "Between-Subjects"` and a documented reason.

- [ ] T006 [US2] In `code/preprocess.py`, implement and EXECUTE the full preprocessing pass on the real raw data (repairing the truncated `run_preprocessing`): load `data/raw/ds000208.parquet` (memory-mapped/chunked if large; memory must stay ≤ 7 GB, FR-005), drop duplicate rows and rows with missing `reaction_time` or `mood_rating`, then within each `condition` group compute the IQR of `reaction_time`, flag rows outside 1.5 × IQR with a boolean `is_outlier` column (FR-002), Z-score normalize `reaction_time` per condition, and write `data/interim/preprocessed_ds000208.csv`.
  - Verification: output CSV contains `is_outlier` and normalized RT columns; a focused unit test in `tests/` confirms IQR thresholds are computed per condition.

- [ ] T007 [US2] Still in `code/preprocess.py`, aggregate `data/interim/preprocessed_ds000208.csv` per `participant_id` × `condition` into mean normalized RT (`rt_mean`) and mean mood (`mood_mean`), propagating `age`/`gender` where present; write `data/processed/analysis_ready_ds000208.csv` (conforming to the extended dataset schema). Produce the outlier audit trail `data/interim/outlier_log.json` as a non-empty list of per-condition objects `{condition, iqr_lower, iqr_upper, flagged_count}` (repairing the previous empty `[]` output).
  - Verification: `analysis_ready_ds000208.csv` has one row per participant-condition; `outlier_log.json` contains entries for both conditions with integer `flagged_count > 0` or an explicitly documented zero.

## Phase 2: Complete the study and validate its evidence

- [ ] T008 [US3] In `code/analyze.py`, load `data/processed/analysis_ready_ds000208.csv` and `data/interim/design_branch.json`; for each outcome (RT, mood) run a **One-Way ANOVA** (`scipy.stats.f_oneway`), or ANCOVA with age/gender covariates where present. Run Shapiro-Wilk normality and Levene homogeneity checks; on assumption failure apply (i) log-transformation for skewed RT, (ii) Welch's ANOVA for heteroscedasticity, (iii) Kruskal-Wallis fallback, documenting each decision (FR-007, FR-008). Report convergence warnings and effect-size confidence intervals when N < 30 per condition (spec edge case). Compute eta-squared effect sizes. Write raw statistics to `results/analysis_raw.json`.
  - Verification: JSON contains F, p_raw, effect size, assumption-check outcomes, and the documented test-selection decision for each outcome.

- [ ] T009 [US3] In `code/analyze.py`, apply Benjamini-Hochberg FDR correction across all outcome p-values (FR-004), producing `p_fdr` values; perform the α-sensitivity sweep over {0.01, 0.05, 0.1} recording significance booleans per outcome (FR-006, SC-004); write `results/analysis_output.json` conforming to `contracts/analysis_output.schema.yaml` (per outcome: `test_type`, `design_type`, `f_value`, `p_raw`, `p_fdr`, `effect_size`, `alpha_sensitivity`). Add a check in `tests/verify_fdr.py` asserting `p_fdr >= p_raw` for every entry (SC-003 — note the mathematically correct direction; the spec's `p_fdr ≤ p_raw` phrasing is flagged for amendment, not enforced) and write `results/fdr_verification.json`.
  - Verification: `results/analysis_output.json` validates against the contract schema; `tests/verify_fdr.py` passes.

- [ ] T010 [US3] Conduct the two sensitivity analyses: (a) outlier sensitivity — re-run the ANOVA with outliers retained vs. removed, recording differences in effect sizes and p-values in `results/outlier_sensitivity.json`; (b) a priori power analysis for a two-group Between-Subjects ANOVA at Cohen's d = 0.5, α = 0.05, power = 0.80 (computed with `statsmodels.stats.power`, not G*Power), recording required N and the actual achieved N in `results/power_analysis.txt`. Compare achieved N against the required N and record adequacy.
  - Verification: both artifacts exist with real computed values; power analysis states required N and actual N.

- [ ] T011 [US3] In `code/report.py`, consolidate `results/analysis_output.json`, `data/interim/design_branch.json`, `results/outlier_sensitivity.json`, and phrasing-check flags into `results/analysis_results.json` conforming to `contracts/analysis_results.schema.yaml` (`design_type`, `main_test` with 95% CI for the effect size, `sensitivity_analysis` array over the α set, `limitations` with `contains_associational: true` and `modulation_claim_valid`). All numbers must be read directly from the result JSONs (Constitution IV).
  - Verification: `results/analysis_results.json` validates against the contract schema; every reported number traces to a result file.

- [ ] T012 [US3] In `code/report.py`, render `paper/report.md` from the validated results containing: (a) the design type ("Between-Subjects"), (b) ANOVA (or non-parametric) tables with raw and FDR-corrected p-values, (c) the sensitivity table covering α ∈ {0.01, 0.05, 0.1}, (d) a Limitations section containing the exact phrase **"associational"** and stating that no verified open reward-feedback dataset exists so modulation by reward feedback could not be tested, (e) a Results section that does NOT contain the word "causal" (FR-003), and (f) the explicit statement that "Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed" (FR-009). Verify the phrasing constraints programmatically and abort with a non-zero exit code if violated.
  - Verification: `paper/report.md` exists; automated phrasing check passes ("associational" present in Limitations, "causal" absent from Results, proxy statement present).

## Phase 3: Reproducible results and paper handoff

- [ ] T013 [US2] [US3] Add runtime and memory instrumentation to the pipeline entry point (`code/pipeline.py`): record wall-clock start/end times and peak memory usage across the full run, write `results/runtime_report.json` with `total_seconds`, `peak_ram_gb`, and a boolean `runtime_ok` (total ≤ 21,600 s and peak RAM ≤ 7 GB) satisfying FR-005 and SC-002. Run the complete pipeline end-to-end from the documented command in `quickstart.md` and confirm all prior artifacts are regenerated from real inputs.
  - Verification: `results/runtime_report.json` shows `runtime_ok: true`; re-running the documented command reproduces the result files.

- [ ] T014 [US1] [US2] [US3] Write the focused test suite in `tests/` and run it with `pytest`: unit tests for IQR outlier flagging (per-condition), Z-score normalization, BH correction monotonicity (`p_fdr >= p_raw`), α-sensitivity coverage, and phrasing constraints on the rendered report; an integration test that runs the pipeline on the real downloaded data and validates `results/analysis_output.json` and `results/analysis_results.json` against their contracts. Document the paper-stage handoff in `paper/report.md`: the report, result JSONs, outlier-sensitivity and power analyses, and the limitations statement are ready for the paper pipeline (layout, PDF compilation, and publication are subsequent stages).
  - Verification: `pytest tests/` passes; contract validation succeeds; handoff section names the artifacts the paper stage will consume.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstration |
|---|---|---|
| FR-000 (variable validation) | T003, T004 | Ingest exits 0 only with all required variables; `ingest_validation_report.json` |
| FR-001 (halt on missing vars / >7 GB) | T003, T004 | Exit code 1 on failure paths |
| FR-002 (per-condition IQR outliers) | T006, T007 | `outlier_log.json` with per-condition thresholds |
| FR-003 (associational / no "causal") | T012 | Automated phrasing check in report generation |
| FR-004 (BH FDR) | T009 | `p_fdr` column in `analysis_output.json` |
| FR-005 (CPU, ≤7 GB, ≤6 h) | T013 | `runtime_report.json` with `runtime_ok` |
| FR-006 (α sweep) | T009 | `alpha_sensitivity` object |
| FR-007/FR-008 (Between-Subjects design) | T005, T008 | `design_branch.json` + ANOVA selection |
| FR-009 (behavioral-proxy transparency) | T012 | Explicit statement in report |
| SC-001 | T004 | Validation report + exit codes |
| SC-002 | T013 | `runtime_report.json` |
| SC-003 | T009 | `fdr_verification.json` (correct `p_fdr >= p_raw` direction) |
| SC-004 | T009, T012 | Sensitivity coverage of {0.01, 0.05, 0.1} |

**Execution order**: T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014. T001–T002 are complete. No task writes to `state/` or `.github/` (platform-owned); no task downloads ds003392 or fabricates reward data (no verified open source exists — documented as a limitation instead).

## Revision behavior

T001–T002 remain checked (verified scaffolding). Previously rejected tasks T003–T010 from the old list are superseded by the corrected tasks above: the ds003392 download and `state/...` writes are removed as contradicting the active plan; the truncated preprocessing driver and empty outlier log are repaired in T006/T007; the failed analyze run is re-tasked in T008/T009 with the Between-Subjects design the plan mandates.
