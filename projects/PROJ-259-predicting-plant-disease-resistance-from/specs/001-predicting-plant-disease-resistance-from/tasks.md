# Tasks: Predict Plant Disease Resistance from Multi‑omics Data  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and prior verifier feedback.  
Completed tasks (T001–T065) are preserved as‑is; the four verifier‑rejected items have been reopened (T066–T069) and the scientific‑run phase (T070–T077) is pending.

---

## Phase 1–8 : Completed (preserve)

- [ ] T001 Establish project layout, pin dependencies, and write a runnable command in `quickstart.md`.   <!-- FAILED-IN-EXECUTION: scripts/run_quickstart.sh exit=2 -->
    Path: `specs/001-predict-plant-disease-resistance/quickstart.md`  
    **Verification**: Run `make quickstart` and assert that `quickstart_output.txt` exists and contains the expected banner.  

- [ ] T002 Implement core download‑preprocess pipeline (`code/download.py`, `code/preprocess.py`).  
    Path: `code/download.py`, `code/preprocess.py`  
    **Verification**: Execute `python -m code.download` and `python -m code.preprocess` on synthetic data; assert that `data/raw/` and `data/processed/` files are created without error.  

- [X] T003 Connect CLI entry point (`code/cli.py`) and produce a small‑scale result file (`data/results/small_demo.csv`).  
    Path: `code/cli.py`, `data/results/small_demo.csv`  
    **Verification**: Run `python -m code.cli --demo` and check that `small_demo.csv` contains columns `sample_id,feature_1,...,prediction`.  

- [ ] T004 Add unit tests for data‑fetching logic (`tests/unit/test_download.py`).  
    Path: `tests/unit/test_download.py`  
    **Verification**: `pytest -q tests/unit/test_download.py` exits with code 0.  

- [ ] T005 Add integration test for end‑to‑end run on synthetic CI data (`tests/integration/test_e2e_ci.py`).  
    Path: `tests/integration/test_e2e_ci.py`  
    **Verification**: `pytest -q tests/integration/test_e2e_ci.py` succeeds.  

- [ ] T006 Create schema validation tests for `data_manifest.yaml` (`tests/contract/test_dataset_schema.py`).  
    Path: `tests/contract/test_dataset_schema.py`  
    **Verification**: Run the test against `data/data_manifest.yaml`; it must pass.  

- [ ] T007 Write Dockerfile that builds a reproducible container (≤ 6 h runtime).  
    Path: `Dockerfile`  
    **Verification**: Build Docker image and run `docker run <image> echo ok`; build must complete within 6 h.  

- [X] T008 Add resource‑monitor stub (`code/utils/dummy_monitor.py`) – later replaced by real implementation.  
    Path: `code/utils/dummy_monitor.py`  
    **Verification**: Import `dummy_monitor` and call its context manager; no exception should be raised.  

- [ ] T009 Implement basic exception hierarchy (`code/exceptions.py`).  
    Path: `code/exceptions.py`  
    **Verification**: Raise each custom exception and assert the correct error message and exit code.  

- [ ] T010 Create synthetic data generator for CI mode (`code/generate_synthetic.py`).  
    Path: `code/generate_synthetic.py`  
    **Verification**: Run generator; verify output files have expected dimensions (e.g., 200 samples × 500 features).  

- [ ] T011 Wire synthetic generator into CLI (`--ci-mode` flag).  
    Path: `code/cli.py`  
    **Verification**: Execute CLI with `--ci-mode` and confirm synthetic data files are created under `data/synthetic/`.  

- [ ] T012 Add pytest configuration (`pyproject.toml` section).  
    Path: `pyproject.toml`  
    **Verification**: Run `pytest`; configuration should be detected and respected.  

- [ ] T013 Implement basic logging wrapper (`code/utils/logger.py`).  
    Path: `code/utils/logger.py`  
    **Verification**: Emit a log entry and check that `pipeline.log` contains the message with correct level.  

- [ ] T014 Create placeholder performance benchmark script (`scripts/perf_dummy.sh`).  
    Path: `scripts/perf_dummy.sh`  
    **Verification**: Run script; ensure it produces a non‑empty `perf_dummy.log`.  

- [ ] T015 Add stratified split utility (`code/utils/split.py`).  
    Path: `code/utils/split.py`  
    **Verification**: Split a toy dataset and assert class proportions are preserved in each fold.  

- [ ] T091 Add unit test for stratified split utility (`tests/unit/test_stratified_split.py`).  
    Path: `tests/unit/test_stratified_split.py`  
    **Verification**: Run `pytest -q tests/unit/test_stratified_split.py` and assert that each generated split preserves the original class distribution within a tolerance of 1 %.  

- [ ] T016 Implement LASSO‑based feature selector (`code/feature_selection.py`).  
    Path: `code/feature_selection.py`  
    **Verification**: Run selector on synthetic data; output feature list must be non‑empty.  

- [ ] T017 Implement Gradient‑Boosting classifier wrapper (`code/model_training.py`).  
    Path: `code/model_training.py`  
    **Verification**: Fit model on a small synthetic dataset; ensure a model file `model.pkl` is written.  

- [ ] T018 Add permutation‑test helper (`code/utils/permutation.py`).  
    Path: `code/utils/permutation.py`  
    **Verification**: Run helper with fixed seed; assert returned p‑value lies in [0,1] and is reproducible.  

- [ ] T019 Create VIF calculation utility (`code/utils/vif.py`).  
    Path: `code/utils/vif.py`  
    **Verification**: Compute VIF on a test matrix; confirm numeric values and that any VIF > 5 is flagged.  

- [ ] T020 Write CI‑mode end‑to‑end script (`scripts/run_ci.sh`). *(environment variables only; real monitor added later)*  
    Path: `scripts/run_ci.sh`  
    **Verification**: Execute script in CI mode; it must exit with code 0.  

- [ ] T021 Add sanity‑check tests for VIF flagging (`tests/unit/test_vif.py`).  
    Path: `tests/unit/test_vif.py`  
    **Verification**: Test passes and confirms correct flagging logic.  

- [ ] T022 Add sanity‑check tests for permutation p‑value (`tests/unit/test_permutation.py`).  
    Path: `tests/unit/test_permutation.py`  
    **Verification**: Test asserts p‑value is within [0,1].  

- [ ] T023 Create CSV writer for selected‑feature table (`code/utils/io.py`).  
    Path: `code/utils/io.py`  
    **Verification**: Write CSV; check header row matches expected columns.  

- [ ] T024 Add documentation stub for data‑manifest (`docs/data_manifest.md`).  
    Path: `docs/data_manifest.md`  
    **Verification**: Build docs and ensure no broken links.  

- [ ] T025 Create placeholder final‑report generator (`code/generate_final_report.py`). *(truncated – replaced by T067)*  
    Path: `code/generate_final_report.py`  
    **Verification**: (Will be replaced by final implementation in T067.)  

- [ ] T026 Add basic resource‑usage logger (`code/utils/resource_logger.py`). *(stub – replaced by T066)*  
    Path: `code/utils/resource_logger.py`  
    **Verification**: Run logger on dummy stage; JSON output must contain `peak_rss_gb` and `runtime_seconds`.  

- [ ] T027 Add unit test for model‑output schema (`tests/contract/test_model_output_schema.py`).  
    Path: `tests/contract/test_model_output_schema.py`  
    **Verification**: Test validates `artifacts/reports/model_output.json` against schema.  

- [ ] T028 Add unit test for pipeline‑output schema (`tests/contract/test_output_schema.py`).  
    Path: `tests/contract/test_output_schema.py`  
    **Verification**: Test validates `artifacts/reports/pipeline_output.json` against schema.  

- [ ] T029 Add script to compute and log collinearity diagnostics (`scripts/collinearity.sh`).  
    Path: `scripts/collinearity.sh`  
    **Verification**: Run script; ensure `collinearity.log` is produced.  

- [ ] T030 Add CI‑mode benchmark log collector (`scripts/collect_benchmark.sh`).  
    Path: `scripts/collect_benchmark.sh`  
    **Verification**: Execute; verify `benchmark_log.txt` is non‑empty.  

- [ ] T031 Add stratified‑shuffle‑split wrapper (`code/utils/stratified_split.py`).  
    Path: `code/utils/stratified_split.py`  
    **Verification**: Split dataset; assert class balance is maintained.  

- [ ] T032 Add sanity‑check for dataset power calculator (`code/utils/power_calc.py`).  
    Path: `code/utils/power_calc.py`  
    **Verification**: Run calculator; output must be a numeric power estimate.  

- [ ] T033 Add unit test for power‑calc (`tests/unit/test_power_calc.py`).  
    Path: `tests/unit/test_power_calc.py`  
    **Verification**: Test passes confirming numeric output.  

- [ ] T034 Add script to generate exclusion‑log (`scripts/generate_exclusion_log.sh`).  
    Path: `scripts/generate_exclusion_log.sh`  
    **Verification**: Run script; `exclusion_log.csv` must be non‑empty.  

- [ ] T035 Add integration test for full pipeline on synthetic data (`tests/integration/test_full_pipeline_ci.py`).  
    Path: `tests/integration/test_full_pipeline_ci.py`  
    **Verification**: Test runs end‑to‑end on synthetic data and exits with code 0.  

- [ ] T036 Add README entry for reproducibility checklist (`docs/reproducibility_checklist.md`).  
    Path: `docs/reproducibility_checklist.md`  
    **Verification**: Build checklist markdown; ensure it renders without errors.  

- [ ] T037 Add script to compute stability of feature selection across thresholds (`scripts/feature_stability.sh`).  
    Path: `scripts/feature_stability.sh`  
    **Verification**: Run script; confirm PNG `feature_stability.png` is created.  

- [ ] T038 Add unit test for stability script (`tests/unit/test_feature_stability.py`).  
    Path: `tests/unit/test_feature_stability.py`  
    **Verification**: Test passes and verifies PNG output exists.  

- [ ] T039 Add placeholder for external‑validation runner (`code/validation.py`).  
    Path: `code/validation.py`  
    **Verification**: Added unit test `tests/unit/test_external_validation.py` that imports the module, runs it on a tiny synthetic dataset, and asserts JSON schema compliance.  

- [ ] T040 Add unit test for external‑validation logic (`tests/unit/test_validation.py`).  
    Path: `tests/unit/test_validation.py`  
    **Verification**: Test passes confirming correct JSON output.  

- [ ] T041 Add script to compute null‑baseline performance (`scripts/null_baseline.sh`).  
    Path: `scripts/null_baseline.sh`  
    **Verification**: Execute; ensure numeric baseline metric is written to `null_baseline.json`.  

- [ ] T042 Add data‑manifest generation with real‑data fallback logic (see plan notes).  
    Path: `code/download.py`  
    **Verification**: Run manifest generation; assert `data/data_manifest.yaml` is created with required fields. If real data are missing, pipeline must halt with `EX_DATA_INTEGRITY`.  

- [ ] T043 Add unit test for manifest generation (`tests/unit/test_manifest.py`).  
    Path: `tests/unit/test_manifest.py`  
    **Verification**: Test validates generated manifest against `dataset.schema.yaml`.  

- [ ] T044 Add script to visualize VIF heatmap (stub – replaced by final implementation in T075).  
    Path: `scripts/vif_heatmap.sh`  
    **Verification**: (Will be replaced by final implementation in T075.)  

- [ ] T045 Add assertion that hold‑out indices are never used in training (implemented in `code/model_training.py`).  
    Path: `code/model_training.py`  
    **Verification**: Unit test confirms no overlap between training and hold‑out sets.  

- [ ] T046 Add resource monitor implementation (`code/utils/resources.py`). *(later refined by T066)*  
    Path: `code/utils/resources.py`  
    **Verification**: Run monitor on a dummy stage; JSON report must include `peak_rss_gb` and `runtime_seconds`.  

- [ ] T047 Add reproducibility seed manager (`code/utils/seed.py`).  
    Path: `code/utils/seed.py`  
    **Verification**: Run two separate pipelines; ensure random seeds produce identical results.  

- [ ] T048 Add double‑run permutation reproducibility check (`tests/integration/test_permutation_repeat.py`).  
    Path: `tests/integration/test_permutation_repeat.py`  
    **Verification**: Test runs permutation twice with same seed; asserts identical p‑values.  

- [ ] T049 Add CI‑mode synthetic‑data sanity test (`tests/unit/test_synthetic.py`).  
    Path: `tests/unit/test_synthetic.py`  
    **Verification**: Test passes confirming synthetic data shape and content.  

- [ ] T050 Add script to archive intermediate artefacts (`scripts/archive_artifacts.sh`).  
    Path: `scripts/archive_artifacts.sh`  
    **Verification**: Run script; check that specified artefacts are moved to `archive/`.  

- [ ] T051 (removed – reopened as T066)  

- [ ] T052 Add documentation for streaming strategy (`docs/streaming_strategy.md`).  
    Path: `docs/streaming_strategy.md`  
    **Verification**: Build doc; ensure no broken links.  

- [ ] T053 (removed – reopened as T067)  

- [ ] T054 Add unit test for streaming loader (`tests/unit/test_streaming.py`).  
    Path: `tests/unit/test_streaming.py`  
    **Verification**: Test passes and validates streamed data shape.  

- [ ] T055 (removed – reopened as T068)  

- [ ] T056 Add CI‑mode benchmark summary generator (`scripts/benchmark_summary.sh`).  
    Path: `scripts/benchmark_summary.sh`  
    **Verification**: Run script; verify `benchmark_summary.csv` is produced.  

- [ ] T057 (removed – reopened as T069)  

- [ ] T058 Add script to compare model vs null baseline (`scripts/compare_null.sh`).  
    Path: `scripts/compare_null.sh`  
    **Verification**: Execute; ensure JSON contains both model and null metrics.  

- [ ] T059 Add unit test for null‑baseline comparison (`tests/unit/test_null_baseline.py`).  
    Path: `tests/unit/test_null_baseline.py`  
    **Verification**: Test passes and validates JSON schema.  

- [ ] T060 Add final figure generation stub (`scripts/generate_figures.sh`).  
    Path: `scripts/generate_figures.sh`  
    **Verification**: Run stub; placeholder PNG files are created.  

- [ ] T061 Add unit test for VIF flag thresholds (`tests/unit/test_vif_flags.py`).  
    Path: `tests/unit/test_vif_flags.py`  
    **Verification**: Test confirms correct boolean flagging for VIF > 5.  

- [ ] T062 Add documentation for reproducibility checklist updates (`docs/reproducibility_checklist.md`).  
    Path: `docs/reproducibility_checklist.md`  
    **Verification**: Build checklist; verify it lists exact seeds and software versions.  

- [ ] T063 Add script to compute confidence intervals for performance metrics (`scripts/confidence_interval.sh`).  
    Path: `scripts/confidence_interval.sh`  
    **Verification**: Run script; `confidence_interval.json` must contain `lower` and `upper`.  

- [ ] T064 Add unit test for confidence‑interval script (`tests/unit/test_confidence_interval.py`).  
    Path: `tests/unit/test_confidence_interval.py`  
    **Verification**: Test passes confirming JSON fields.  

- [ ] T065 Add final CI pipeline orchestrator (`scripts/run_full_ci.sh`).  
    Path: `scripts/run_full_ci.sh`  
    **Verification**: Execute; all prior scripts run without error.  

---

## Phase 9 : Repair verifier‑rejected tasks  

- [ ] T080 Create core pipeline driver (`code/main.py`) that imports the resource monitor (`code/utils/measure_resources.py`) and orchestrates all stages.  
    Path: `code/main.py`  
    **Verification**: Import `code.main` and run with `--ci-mode`; ensure monitor activates and JSON report is generated.  

- [ ] T066 [US1] Implement real resource‑monitor `code/utils/measure_resources.py` (context‑manager that records peak RSS and wall‑time, reads `MAX_MEMORY_GB` & `MAX_RUNTIME_HOURS` from the environment, raises `EX_RESOURCE_LIMIT (04)` if limits are exceeded).  
    *Import* it in `code/main.py` so every pipeline stage runs under the monitor.  
    Update `scripts/run_ci.sh` to export `MAX_MEMORY_GB=7` and `MAX_RUNTIME_HOURS=6`.  
    **Verification**: `python -m code.main --ci-mode` creates `artifacts/reports/performance_benchmark.json` containing per‑stage `peak_rss_gb` and `runtime_seconds`. Also validated against `performance_benchmark.schema.yaml`.  

- [ ] T067 [US1] Complete `code/generate_final_report.py` so it aggregates all JSON/CSV artefacts from `artifacts/reports/` (metrics, holdout_metrics, selection_frequency, biomarker_summary, permutation_comparison) and writes a comprehensive markdown report `artifacts/reports/final_validation_report.md`.  
    *Fix* `load_json_file` to point at `artifacts/reports/`.  
    Report sections: CV performance vs null baseline, permutation p‑value, biomarker counts vs SC‑002, VIF flags, resource usage, and a provenance statement (`REAL_DATA` or `SIMULATED_DATA`).  
    **Verification**: Running the generator (both CI and real modes) produces a non‑empty markdown file with all listed sections and values matching source artefacts.  

- [ ] T068 [US2] Add project‑local linting configuration (no `.github/` workflow).  
    Create a `pyproject.toml` `[tool.black]` and `[tool.flake8]` section (line‑length 100, exclude `data/`).  
    Add `scripts/lint.sh` that runs `flake8 code tests` and `black --check code tests`.  
    **Verification**: `bash scripts/lint.sh` exits with status 0, writes stdout/stderr to `artifacts/reports/lint_log.txt`, and the log contains the string `no issues found`.  

- [ ] T069 [US2] Add `tests/test_exceptions.py` with unit tests that trigger each custom exception (`EX_DATA_INTEGRITY (02)`, `EX_POWER_INSUFFICIENT (03)`, `EX_RESOURCE_LIMIT (04)`) and assert the exact mandated message strings and exit codes.  
    **Verification**: `pytest -q tests/test_exceptions.py` passes, confirming messages and codes.  

- [ ] T081 [US1] Verify Success Criterion SC‑002: after feature selection, parse `results/selected_features.csv` and assert ≥ 10 SNPs and ≥ 10 metabolites have BH‑adjusted p < 0.05.  
    **Verification**: Test script exits with code 0 only if counts meet threshold; otherwise fails.  

- [ ] T082 [US1] Verify Success Criterion SC‑003: read `artifacts/reports/model_output.json` and assert `validation.permutation_p_value` ≤ 0.05.  
    **Verification**: Test passes only when p‑value ≤ 0.05.  

- [ ] T083 [US1] Verify Success Criterion SC‑004: parse `artifacts/reports/performance_benchmark.json` and assert `runtime_seconds` ≤ 21600 (6 h) and `peak_rss_gb` ≤ 7.0.  
    **Verification**: Test fails if limits are exceeded.  

- [ ] T084 [US3] Verify external validation output (if second dataset exists): ensure `artifacts/reports/external_validation.json` contains required performance fields and that the ≥ 75 % target is reported.  
    **Verification**: Test checks JSON schema and target compliance.  

- [ ] T085 [US2] Verify final result figures (T075) conform to expected formats: PNG for VIF heatmap, PNG for stability plot, TSV for top features.  
    **Verification**: Simple file‑existence and header checks.  

---

## Phase 10 : Real‑data scientific run (SC‑001 – SC‑003)

- [ ] T070 [US1] Identify a REAL public dataset containing paired genotype (SNP), metabolomics, and resistance phenotype for ≥ 100 samples. Record accession IDs, URLs, and query strings in `data/data_manifest.yaml` (schema `dataset.schema.yaml`). If no such dataset exists, document the precise gap in `docs/real_data_search.md` and **halt** (no synthetic substitution).  

- [ ] T071 [US1] Download the dataset identified in T070 into `data/raw/` using reproducible commands (`pysradb`/SRA‑Toolkit for reads, direct HTTP fetch for metabolomics tables). Compute SHA‑256 checksums, store them in `data/data_manifest.yaml`, and **fail loudly** on any fetch error (no fallback). For large files, stream in chunks as described in `docs/streaming_strategy.md`.  

- [ ] T072 [US1] Run `code/preprocess.py` on the real raw data to (a) call variants / build SNP matrix, (b) normalize metabolomics (MetaboAnalyst‑compatible), (c) align samples across all three modalities, and (d) log excluded samples to `data/processed/exclusion_log.csv`. Enforce FR‑007/FR‑008 halts if < 100 paired samples remain.  

- [ ] T073 [US1] Execute the full scientific pipeline (`python -m code.main`) on the real aligned data (no `--ci-mode`):  
    * stratified split (FR‑009)  
    * nested feature selection with BH correction and sensitivity sweep {0.01, 0.05, 0.1} (FR‑003)  
    * Elastic‑Net (continuous) **or** Gradient‑Boosting (categorical) with 5‑fold CV and null‑baseline (FR‑004)  
    * permutation test (n = 1000, seed 42) on hold‑out set, VIF calculation (flag > 5) (FR‑005)  
    All artefacts written under `artifacts/reports/` and validated against `model_output.schema.yaml` and `output.schema.yaml`.  

- [ ] T074 [US3] If a second independent real dataset with matching modalities exists (identified during T070), run external validation (`python -m code.main --validate-external <path>`) and write `artifacts/reports/external_validation.json` with the same metric suite and a statement whether the ≥ 75 % target holds. If no second dataset exists, record the limitation in `docs/real_data_search.md` and in the final report.  

---

## Phase 11 : Results synthesis and paper handoff

- [ ] T075 [US2] Generate final result tables and figures **from the real‑data run only**:  
    * `artifacts/figures/vif_heatmap.png` (real selected features)  
    * Feature‑stability plot of selection frequency across thresholds  
    * Summary table `artifacts/figures/top_features.tsv` listing top SNPs & metabolites with BH‑adjusted p‑values, effect sizes, and selection frequencies.  
    All figures/tables are produced programmatically from the JSON/CSV artefacts (single source of truth).  
    **Verification**: Test scripts confirm PNG and TSV files exist and contain required columns/headers.  

- [ ] T076 Write a concise methods‑and‑results narrative in `docs/results_summary.md`. The document must:  
    * cite dataset accession IDs from `data/data_manifest.yaml`  
    * report sample counts after exclusion, CV performance vs null baseline, permutation p‑value, biomarker counts vs SC‑002, VIF findings, resource usage vs SC‑004  
    * honestly note any unmet success criteria (e.g., CV < 75 % or < 10 significant biomarkers)  
    * include a “Paper‑stage handoff” section describing how the paper should reference the generated artefacts and that all findings are associational.  
    **Verification**: Lint markdown for required sections and citations.  

- [ ] T077 Re‑run the entire documented workflow from scratch (real‑data path, then `--ci-mode` path) and verify:  
    * All `pytest` suites pass (including `tests/test_exceptions.py`)  
    * Linting passes (`bash scripts/lint.sh`) and `lint_log.txt` contains `no issues found`  
    * `code/generate_final_report.py` produces `final_validation_report.md` for both modes  
    * The reproducibility checklist (`docs/reproducibility_checklist.md`) lists exact seeds, software versions, and data‑accession provenance.  
    * Record the exact commands and their outputs in `docs/results_summary.md`.  
    **Verification**: Automated script checks all above conditions and exits with 0 only on full success.  

---

### Dependency & Requirement Coverage (summary)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 / FR‑002 | T070, T071, T072 |
| FR‑003 | T073 |
| FR‑004 | T073 |
| FR‑005 | T073 |
| FR‑006 | T080, T066, T077 |
| FR‑007 / FR‑008 | T069 (tests) & T072 (enforcement) |
| FR‑009 | T073 |
| SC‑001 – SC‑004 | Evaluated in T073‑T076 (resource monitor T080/T066 enforces limits; verification tasks T081‑T084 check criteria) |
| Linting | T068 |
| Exception handling | T069 |
| Real‑data provenance | T070‑T074 |
| Final report & handoff | T067, T075‑T077 |

---  

*All tasks above follow the canonical `- [ ] T### [P?] [USx?] description` format, include exact artifact paths in indented continuation lines, and respect the data‑flow ordering required by the specification.*  
