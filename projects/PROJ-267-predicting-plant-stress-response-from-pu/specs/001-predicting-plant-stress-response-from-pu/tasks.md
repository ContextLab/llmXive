# Tasks: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`dataset.schema.yaml`, `model_output.schema.yaml`), original idea, prior tasks.md and verifier feedback.
**Branch**: `001-predict-plant-stress-response`

This is a consolidation re-plan. Verified, completed work is preserved with its original task IDs and checked status. Rejected/unverifiable tasks are re-scoped so each deliverable is a real, deterministically checkable artifact. Related pending work is grouped into substantive research tasks following the template's three phases (first end-to-end analysis → complete validation → results handoff). Directory-creation and generic tooling tasks are folded into the tasks that need those artifacts.

## Phase 1: Setup and first end-to-end analysis

**Goal**: A runnable pipeline that fetches real paired proteomic/transcriptomic data and produces a first real result row set.

- [ ] T001 [US1] Establish project skeleton and runnable entry point in one verifiable step: create `code/`, `code/data_ingestion/`, `code/modeling/`, `code/reporting/`, `code/utils/`, `tests/unit/`, `data/raw/`, `data/processed/`, `results/`, `logs/`, `docs/`, plus `code/requirements.txt` (pandas, numpy, scikit-learn, matplotlib, seaborn, rpy2, requests, psutil, datasets, pytest; pinned versions) and `code/main.py` with a `--stage` argument. **Verification**: a directory tree listing (`find . -type d`) committed as `docs/structure.txt`, and `python -m code.main --stage noop` exits 0 after `pip install -r code/requirements.txt`. Document the runnable command in the feature's `quickstart.md`.  
    - **Constraint**: If `rpy2`/R/biomaRt (version 2023-10) cannot be installed, HALT with "Tooling Unavailable" — do not silently substitute a mapping method. If `imp3` is missing, use the custom MinProb LCM implementation in `code/utils/lcm.py`; never fall back to sklearn mean/iterative imputation. Log deviations in `docs/deviation_log.md`. (FR-002, FR-003; Constitution VII.)

- [ ] T002 [P] [US1] Implement real-data ingestion with loud failure in `code/data_ingestion/download.py`: read the verified GEO/ProteomeXchange URLs from `research.md`, validate domains (ncbi.nlm.nih.gov, proteomexchange.org, ebi.ac.uk), stream large files (`datasets.load_dataset(..., streaming=True)` or chunked HTTP download) so full real datasets are processed without exceeding ~7 GB RAM, select the largest‑n dataset per species/stress pair (ties broken by earliest publication date), and write raw files with SHA‑256 checksums via `code/utils/checksums.py` (existing, verified). **Verification**: `data/raw/` contains real downloaded files > 1 KB each with a committed `data/raw/checksums.sha256`; a failing URL raises an exception (no `try/except` fallback to synthetic/mock data anywhere in the module). (FR-001; repairs rejected T041; preserves verified T040 streaming refactor.)

- [ ] T003 [US1] Implement preprocessing and merge producing the unified matrix: extend `code/data_ingestion/normalize.py` (low‑abundance filter < 50 % detection, MinProb LCM imputation) and `code/data_ingestion/merge.py` (biomaRt UniProt→Ensembl mapping via rpy2, drop‑and‑log unmatched rows), orchestrated by `code/data_ingestion/pipeline.py` with ambiguous‑metadata flagging/exclusion logged to `logs/pipeline.log`. **Depends on**: T002 must have completed successfully. Add schema validation of `data/processed/unified_matrix.csv` against `specs/001-predicting-plant-stress-response-from-pu/contracts/dataset.schema.yaml` (dict/Pydantic checks in `code/utils/schema_check.py`). **Verification**: `data/processed/unified_matrix.csv` exists, is non‑empty, passes schema validation, and contains only confirmed stress labels; exclusion/drop counts appear in `logs/pipeline.log`. (FR-002, FR-003; folds in rejected T005, T006 logging setup, T014 orchestration; preserves verified T012–T014 logic.)

- [ ] T004 [US1] Run the data‑verification and feasibility gate end‑to‑end: execute `code/data_ingestion/sanity_check.py` (verified — rejects any synthetic/placeholder values), `code/data_ingestion/sample_check.py` (verified — enforces n ≥ 5 per species/stress pair, excludes failing pairs, flags 5 ≤ n < 50 as **insufficient for 5‑fold CV** and writes `results/cv_strategy.json` with a status of `insufficient`, causing the pipeline to halt), and `code/data_ingestion/completeness.py` (verified — writes `results/data_completeness.json`, SC‑004). **Verification**: `results/sample_stats.json`, `results/cv_strategy.json`, `results/data_completeness.json` all exist with real measured counts; if no valid paired data exists, the pipeline halts with the documented "Data Unavailable" report instead of fabricating. (SC‑004; preserves verified T035–T037, T018.)

**Checkpoint**: `python -m code.main --stage data` runs ingestion → preprocessing → gate on real inputs and produces the unified matrix plus gate JSONs. Do not proceed to modeling until this checkpoint passes.

## Phase 2: Complete the study and validate its evidence

**Goal**: Train, validate, and stress‑test the models on the full verified dataset, preserving every baseline and control from the specification.

- [ ] T005 [US2] Run within‑stress model training on the real unified matrix using the verified modules: `code/modeling/strategy_selector.py`, `code/modeling/hyperparameter_config.py`, `code/modeling/train.py` (RandomForestRegressor + SVR, CPU‑only, **strict 5‑fold cross‑validation**; if the dataset does not contain at least 5 samples per fold the task aborts with a clear error), all preprocessing inside each fold, with `code/modeling/checkpoint.py` saving partial results per fold and sample‑size/CV‑strategy logging to `logs/pipeline.log`. Add a pre‑flight check in `code/main.py` that `data/processed/unified_matrix.csv` exists and is non‑empty before training, halting with "Data Dependency Error" otherwise. **Verification**: `results/within_stress_metrics.json` contains per‑fold R² and RMSE for both models computed from real data. (FR-004, FR-005, SC‑005.)

- [ ] T006 [US2] Run cross‑stress evaluation and all baselines/controls using the verified modules: `code/modeling/cross_stress_eval.py` (train on stress A, test on stress B with actual measured gene expression as ground truth), `code/modeling/baselines.py` (Raw Feature Baseline, T020a), the stress‑label permutation control (1000 iterations, `results/shuffle_control.json`, T021b), `code/modeling/evaluate.py` (null/mean model, `results/null_model_metrics.json`, T021a), and `code/modeling/metrics.py` (Drop_Cross and Drop_Raw to `results/r2_drop.json`, T020c). Apply the permutation test with Bonferroni correction across stress pairs. **Verification**: all five JSON artifacts exist with real metrics; `Drop_Raw` sign‑checked with warning logged if negative. (FR-005, SC‑001, SC‑002.)

- [ ] T007 [US2] Extract and rank feature importance: run the verified `code/modeling/feature_importance.py` to produce the top‑20 protein list per model, validated against `model_output.schema.yaml`'s `feature_importance` contract (max 20 items, protein_id + importance_score). **Verification**: `results/feature_importance.json` exists, conforms to the contract, and importance scores come from the trained models (no placeholder values). (FR‑006.)

- [ ] T008 [US3] Implement and execute runtime metrics with hard limit enforcement in `code/reporting/metrics.py`: record total CPU time and peak memory (psutil) to `results/runtime_metrics.json`, include a pre‑write sanity check that input prediction arrays have non‑zero variance and required attributes (rejecting mock/degenerate inputs), and exit non‑zero with "Resource Limit Exceeded" if runtime > 6 h or memory > 7 GB. **Verification**: `results/runtime_metrics.json` exists in the repository with real measured values, and the limit assertion is exercised by a unit test in `tests/unit/test_metrics.py`. (FR‑008, SC‑003; redoes rejected T027, T029.)

- [ ] T009 [US3] Generate all publication‑ready figures from the validated outputs via the verified `code/reporting/plots.py` and `code/reporting/generate_report.py`: prediction scatter (Predicted vs. Actual with regression line and R² annotation) saved as `results/prediction_scatter.png`, cross‑stress performance heatmap, and feature‑importance bar charts, **run after T007** to ensure the feature‑importance artifact is available. **Verification**: all required PNGs exist under `results/`, are generated directly from the metric JSONs (no hand‑typed statistics), and the summary JSON conforms to `model_output.schema.yaml`. (FR‑007.)

- [ ] T010 [US3] Add edge‑case unit tests in `tests/unit/test_pipeline.py` covering the specification's edge cases: all‑missing columns (drop + log), mismatched gene/protein identifiers (drop count logged), samples without matched transcriptomic data (excluded with reason), ambiguous species metadata (skip + warning), and schema violations. **Additionally**, generate a CV‑integrity report `results/cv_integrity_report.json` that records for each fold the exact training‑test split IDs and confirms no overlap, thereby providing concrete evidence for SC‑005. **Verification**: `pytest tests/unit/` passes, and `results/cv_integrity_report.json` exists and validates that circular dependencies are absent. (Spec edge cases; redoes rejected T033.)

## Phase 3: Reproducible results and paper handoff

**Goal**: A reproducible account of the actual results and a clean handoff to the paper stage.

- [ ] T011 Write `README.md` with Installation, Usage (the exact commands from `quickstart.md`), Data Sources (the verified GEO/ProteomeXchange accessions and URLs actually used), and Results sections whose numbers are generated from or linked to `results/*.json` — no hand‑typed statistics. **Depends on**: completion of T008, T009, and T010 (all result artifacts must exist). **Verification**: every statistic in the Results section cites the artifact file it came from. (Redoes rejected T030a; docstrings for public functions in `code/` are included as part of this task's edit pass — redoes rejected T030b.)

- [ ] T012 Re‑run the full documented workflow from its declared inputs (`python -m code.main --stage all` per `quickstart.md`), confirm all unit tests and artifact checks pass, record the run's runtime metrics against the 6 h / 7 GB limits, and write `docs/results_summary.md` describing methods, actual findings (including negative results such as cross‑stress generalization failure or the Data Unavailable halt path, if taken), limitations (associational framing, collinearity, post‑translational regulation sensitivity caveat), and the paper‑stage handoff (figures, tables, and metric JSONs the paper pipeline should consume). **Verification**: a fresh run reproduces the metric JSONs within tolerance and the summary references only actually‑produced artifacts. (Redoes rejected T034; completes the study handoff.)

## Dependencies and requirement coverage

| Requirement | Task(s) | Command demonstrating completion |
|---|---|---|
| FR-001 (download, largest‑n selection) | T002 | `python -m code.main --stage data` → `data/raw/checksums.sha256` |
| FR-002 (filter, LCM imputation) | T003 | `data/processed/unified_matrix.csv` + `logs/pipeline.log` |
| FR-003 (biomaRt merge) | T003 | drop counts in `logs/pipeline.log` |
| FR-004 (RF/SVR on CPU) | T005 | `results/within_stress_metrics.json` |
| FR-005 (CV, cross‑stress, controls) | T005, T006 | `results/cross_stress_metrics.json`, `results/shuffle_control.json` |
| FR-006 (feature importance) | T007 | `results/feature_importance.json` |
| FR-007 (figures) | T009 | `results/prediction_scatter.png` et al. |
| FR-008 (runtime metrics) | T008 | `results/runtime_metrics.json` |
| SC-001 (vs null model) | T006 | `results/null_model_metrics.json` |
| SC-002 (R² drop, baselines) | T006 | `results/r2_drop.json` |
| SC-003 (resource limits) | T008, T012 | `results/runtime_metrics.json` |
| SC-004 (data completeness) | T004 | `results/data_completeness.json` |
| SC-005 (CV integrity, no leakage) | T005, T010 | `results/cv_integrity_report.json`, `pytest tests/unit/` |

**Execution order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T010 → T009 → T011 → T012. T008 and T010 may run in parallel after T007, but T009 must wait for T007; T011 waits for T008, T009, and T010.

## Revision behavior

Verified completed work (T002‑prior env checks, T035–T037, T040, T043, T044, T008/T023/T007‑prior utilities, T009/T010‑prior unit tests, T011–T014 ingestion logic, T018–T022, T024, T026, T028, T030c, T032) is preserved inside the consolidated tasks above; their acceptance criteria are carried forward, not dropped. Rejected tasks (T001a–T001c, T001b, T003, T005, T006, T027, T029, T030a, T030b, T033, T034, T041) are re‑scoped to produce deterministically verifiable artifacts within the consolidated tasks. Linting/formatting (old T003) was removed as non‑scientific scaffolding not required by the specification.
