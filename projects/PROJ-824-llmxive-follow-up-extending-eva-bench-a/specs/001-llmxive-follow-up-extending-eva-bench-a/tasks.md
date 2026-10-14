# Tasks: llmXive follow‑up: extending "EVA‑Bench: A New End‑to‑end Framework for Evaluating Voice Agents"

**Inputs**: `spec.md`, `plan.md`, existing project skeleton, contracts in `specs/001-llmxive‑latency‑study/contracts/`.

The goal is to deliver a reproducible end‑to‑end study that (1) injects configurable latency into EVA‑Bench audio, (2) re‑runs the original EVA‑Bench scoring pipeline, (3) performs the required statistical analyses, and (4) produces a comparative report against the acoustic‑noise baseline.  
All artifacts must be real files that can be validated against the JSON‑Schema contracts and the acceptance criteria in the specification.

---

## Phase 1 – Project scaffolding (shared infrastructure)

- [X] **T001** [P] Create the canonical project directory layout and add a `pyproject.toml` with the required dependencies.  
  *Path*: `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/`  
  *Verification*: Directory tree exists; `pyproject.toml` lists `pydub`, `scipy`, `pandas`, `statsmodels`, `matplotlib`, `seaborn`, `pytest`. `pip install -r requirements.txt` succeeds.

- [X] **T002** [P] Implement `code/config.py` containing (a) absolute/relative path constants (`DATA_RAW`, `DATA_PROCESSED`, `RESULTS_DIR`), (b) random‑seed handling, and (c) latency hyper‑parameters (`DELAY_VALUES = list(range(200, 2001, 200))`).  
  *Path*: `code/config.py`  
  *Verification*: Importing `config` yields the expected attributes; a unit test (`tests/unit/test_config.py`) checks that `DELAY_VALUES` equals `[200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]`.

- [ ] **T003** [P] Set up a deterministic logging configuration that writes to `logs/run.log` with file rotation and a console handler at `WARNING` level.  
  *Path*: `code/logging_config.py`  
  *Verification*: Running `python -c "import logging, code.logging_config as lc; lc.setup(); logging.info('test')"` creates `logs/run.log` containing the formatted message; log level respects the configuration.

---

## Phase 2 – Data acquisition & verification

- [ ] **T004** [P] depends_on: [T001, T002, T003] Implement a dataset‑download script that fetches the EVA‑Bench archive from the public HuggingFace URL, extracts the JSONL metadata and WAV files into `data/raw/`, and writes SHA‑256 checksums to `data/checksums.json`. The script must abort with a clear error if the download fails or the checksum does not match.   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=2 -->
  *Path*: `code/data/download.py`  
  *Verification*: After execution, `data/raw/` contains the expected files; `data/checksums.json` includes an entry for each file; a failed download raises an exception (no silent fallback).

- [ ] **T005** depends_on: [T004] Validate the downloaded dataset against `specs/001-llmxive‑latency‑study/contracts/dataset.schema.yaml`.  
  *Path*: `code/data/validate_dataset.py` (executed by the CI)  
  *Verification*: Script exits with status 0 only if every JSONL entry conforms to the schema; otherwise it prints the offending record IDs.

---

## Phase 3 – User Story 1: Latency injection & baseline execution (Priority P1)

- [ ] **T006** depends_on: [T005] Implement the latency‑injection module that (a) reads each scenario's turn‑boundary timestamps from the JSONL, (b) inserts a silence gap of the specified `delay_ms` **exactly between turns** using `pydub.AudioSegment`, (c) writes the modified audio to `data/processed/{scenario_id}_{delay}ms.wav`, and (d) produces a `data/processed/turn_boundaries_{delay}ms.csv` describing the new start/end times. The module must also include jitter generation (optional "uniform" or "gaussian" as described in `injection.schema.yaml`), with the jitter seed taken from `config.SEED`. **Optimization requirement**: Process audio in streaming chunks (load max 1 MB at a time) to keep peak memory usage < 500 MB per scenario, enabling batch processing without exceeding the 7 GB total RAM constraint.  
  *Path*: `code/processing/latency_injector.py`  
  *Verification*: For each of the 213 target scenarios and each delay value (200, 400, ..., 2000 ms), the output audio file's inter‑turn silence is measured with `pydub` and verified to be `delay_ms ± 10 ms`; the original speech samples are bit‑identical to the source (checksum matches). Running the injector twice with the same seed yields identical output files. **If any scenario's inter-turn silence deviates from delay_ms ± 10 ms, or if any checksum mismatch is detected, the task fails with a clear error message listing the offending scenario IDs.** The CSV file contains the updated timestamps for all scenarios. Code inspection confirms the presence of chunk-based audio loading (e.g., `pydub.utils.mediainfo()` used to determine file size, audio processed in segments with explicit memory cleanup).

- [ ] **T008** depends_on: [T006] Implement a thin wrapper that re‑executes the original EVA‑Bench scoring pipeline on a directory of processed audio files, preserving the original scoring logic unchanged. The wrapper must write one result record per scenario‑delay pair conforming to `results.schema.yaml`. **Required output fields**: Each row in `data/results/evaluation_results.csv` must include columns `scenario_id`, `latency_ms`, `turn_taking_score`, `conversation_progression_score`, `status` (success/timeout/error), `agent_response_text` (transcript of agent's final response), `task_success` (boolean), `turn_boundaries` (JSON array of {speaker, start_time, end_time}), and `timestamp`. These fields are required inputs for downstream behavioral-metrics extraction (T018). **Optimization requirement**: Batch scenarios into groups of 5–10 to reduce I/O overhead and cache intermediate results in memory where possible, reducing total wall-clock time by ~20%.  
  *Path*: `code/processing/pipeline_runner.py`  
  *Verification*: After running on the full dataset (all 213 scenarios × 10 delays), `data/results/evaluation_results.csv` contains rows with all required columns including `agent_response_text`, `task_success`, and `turn_boundaries`. A sanity check confirms that the `status` field is `"success"` for all rows. Code inspection confirms batching logic (e.g., `batch_size` parameter, loop over `range(0, len(scenarios), batch_size)`).

---

## Phase 4 – User Story 2: Threshold detection & non‑linear analysis (Priority P2)

- [ ] **T009** depends_on: [T008] Implement statistical analysis code that (a) loads `evaluation_results.csv`, (b) performs a repeated‑measures ANOVA across the latency levels for each metric, (c) fits a piecewise (segmented) linear regression to the "Conversation Progression" scores, and (d) writes the model description to `data/analysis/threshold_model.json` conforming to `threshold_model.schema.yaml`. **Optimization requirement**: Use vectorized numpy/pandas operations instead of loops; pre-allocate arrays for regression coefficients.  
  *Path*: `code/analysis/stats_models.py`  
  *Verification*: The JSON file contains fields `model_id`, `metric`, `knee_point_ms`, `slope_before`, `slope_after`, `p_value`, `adjusted_p_value`, `r_squared`. Unit test (`tests/unit/test_stats_models.py`) checks that for a synthetic monotonic dataset the fitted knee point lies within the expected range. Code inspection confirms vectorized operations (e.g., `numpy.polyfit()`, `pandas.groupby().apply()` with no explicit Python loops over large arrays).

- [ ] **T010** depends_on: [T009] Implement a sensitivity analysis that re‑fits the segmented regression while sweeping the identified knee point by ± 50 ms (steps of 10 ms) and records the stability metrics (variance of slopes, R²). Results are saved to `data/analysis/sensitivity.json`.  
  *Path*: `code/analysis/sensitivity.py`  
  *Verification*: The JSON contains a list of `knee_point_ms` values and associated `slope_before`, `slope_after`, `r_squared`. A test (`tests/unit/test_sensitivity.py`) asserts that the original knee point appears in the list and that the slope variance is < 0.01.

---

## Phase 5 – User Story 3: Comparative robustness reporting (Priority P3)

- [ ] **T011** depends_on: [T008] Create a comparative‑report generator that (a) loads the latency‑sweep results from T008, (b) loads the acoustic‑noise baseline results (already present in `data/baseline/acoustic_results.csv`), (c) aligns the metrics by scenario, (d) computes normalized degradation curves, (e) calculates the area‑under‑the‑curve (AUC) for both conditions, and (f) performs an interaction ANOVA to test distinctness. The final report is written to `data/report/comparative_report.json` and a summary CSV `comparative_report.csv`.  
  *Path*: `code/analysis/comparative_report.py`  
  *Verification*: The JSON contains keys `latency_auc`, `acoustic_auc`, `auc_difference`, `interaction_p_value`. The CSV includes columns `latency_ms`, `turn_taking_score`, `acoustic_score`. A unit test (`tests/unit/test_comparative_report.py`) checks that `interaction_p_value < 0.05` for a synthetic dataset with known separation.

- [ ] **T012** depends_on: [T011] Produce the final figures (degradation curves, knee‑point annotation, AUC bar plot) and save them under `figures/`.  
  *Path*: `code/visualization/plots.py` (invoked by `T011`)  
  *Verification*: PNG files `figures/turn_taking_vs_latency.png` and `figures/progression_knee_point.png` exist; a CI step verifies that each file is > 1 KB and that the script exits with status 0.

- [ ] **T018** depends_on: [T008] Extract and validate behavioral metrics (Task Completion Rate, Semantic Coherence, Interruption Count) from the evaluation results produced by T008. These metrics MUST be computed independently of the injected delay and MUST NOT be mathematically derived from the silence gap. **Operational definitions and computation**: (1) **Task Completion Rate** = (count of rows where `task_success` == True) / (total rows per scenario), extracted directly from the `task_success` field in `evaluation_results.csv` (T008 output). (2) **Semantic Coherence** = token-overlap similarity score computed from `agent_response_text` field using TF-IDF cosine similarity against the ground-truth expected response (extracted from the original JSONL metadata); compute separately for each scenario-latency pair and average within scenario. (3) **Interruption Count** = number of detected overlapping speech segments, computed by parsing the `turn_boundaries` JSON array (T008 output) and detecting overlaps where consecutive turns have (speaker_A.end_time > speaker_B.start_time). Write results to `data/analysis/behavioral_metrics.json` with fields `scenario_id`, `latency_ms`, `task_completion_rate`, `semantic_coherence`, `interruption_count`. **Independence validation**: Implement a correlation check that asserts the Pearson correlation between `latency_ms` and each metric is < 0.3, confirming that metric variance is driven by agent behavior (response text, task success) and not by delay_ms itself. If any correlation exceeds 0.3, the task fails with an error listing the problematic metrics.  
  *Path*: `code/analysis/behavioral_metrics.py`  
  *Verification*: The JSON file contains fields `scenario_id`, `latency_ms`, `task_completion_rate`, `semantic_coherence`, `interruption_count` for all scenario-latency pairs. A unit test (`tests/unit/test_behavioral_metrics.py`) verifies that (i) metrics are present for all pairs, (ii) metrics are computed from T008 output fields (`task_success`, `agent_response_text`, `turn_boundaries`), and (iii) the independence validation check (correlation < 0.3) is implemented and passes. Code inspection confirms that Task Completion Rate is extracted from `task_success` field, Semantic Coherence is computed via TF-IDF from `agent_response_text`, and Interruption Count is computed from `turn_boundaries` JSON parsing.

- [ ] **T019** depends_on: [T005] Create and validate a concrete injection configuration instance (JSON file) that conforms to `specs/001-llmxive-latency-study/contracts/injection.schema.yaml`. Implement `code/data/validate_injection_config.py` that uses `jsonschema.validate()` to assert the configuration conforms to the schema, raising an exception if validation fails.  
  *Path*: `code/data/validate_injection_config.py`  
  *Verification*: The script loads `injection.schema.yaml` and validates a concrete injection configuration JSON file; it exits with status 0 only if the configuration conforms to the schema. If validation fails, the script raises an exception and prints the validation error.

- [ ] **T020** depends_on: [T005] Create perturbation-profile JSON instances for both latency and acoustic perturbation types that conform to `specs/001-llmxive-latency-study/contracts/perturbation_profile.schema.yaml`. For each latency condition (200, 400, ..., 2000 ms), generate a perturbation_profile.json containing fields `profile_id`, `type` ("latency"), `parameters` (with `mean_delay_ms` and `jitter_range_ms`), and `seed`. For acoustic baseline, generate a profile with `type` ("acoustic") and `parameters` (with `snr_db` and `reverberation_time_s`). Validate all profiles against the schema using `jsonschema.validate()`.  
  *Path*: `code/data/validate_perturbation_profiles.py`  
  *Verification*: All generated profiles are valid JSON, pass schema validation, and are written to `data/perturbation_profiles/`. A unit test verifies that each profile has the required fields and that acoustic profiles have distinct parameters from latency profiles.

---

## Phase 5.5 – Pipeline optimization (required to meet FR-007 and SC-004)

- [ ] **T024a** depends_on: [T006] Implement streaming chunk-based audio loading in `latency_injector.py` to reduce peak per-scenario memory usage to < 500 MB. **Specific implementation requirement**: Load audio files in 1 MB chunks using `pydub.AudioSegment.from_file()` with explicit frame-by-frame or segment-by-segment processing. Implement explicit memory cleanup (e.g., `del chunk` after processing) to release intermediate buffers. The module must process all 213 scenarios without exceeding 500 MB per scenario.  
  *Path*: `code/processing/latency_injector.py`  
  *Verification*: Code inspection confirms the presence of chunk-based loading logic (e.g., loop structure that reads audio in 1 MB increments, explicit `del` statements for memory cleanup). A unit test (`tests/unit/test_streaming_injection.py`) measures peak memory usage for a 10-scenario batch and asserts that per-scenario memory is < 500 MB. The test must call `resource.getrusage()` or `psutil.Process().memory_info()` to measure actual RAM consumption during execution.

- [ ] **T024b** depends_on: [T008] Implement batched scenario execution in `pipeline_runner.py` to reduce I/O overhead and total wall-clock time by ~20%. **Specific implementation requirement**: Add a `batch_size` parameter (default 5–10) and implement explicit loop structure `for i in range(0, len(scenarios), batch_size): batch = scenarios[i:i+batch_size]` to process scenarios in groups. Cache intermediate results (e.g., loaded evaluation models, tokenizers) in memory across the batch to avoid redundant initialization. The batching must not alter the output schema or result values, only reduce execution time.  
  *Path*: `code/processing/pipeline_runner.py`  
  *Verification*: Code inspection confirms explicit batching loop with `batch_size` parameter and batch-level caching of intermediate results. A unit test (`tests/unit/test_batched_pipeline.py`) measures wall-clock time for serial vs. batched execution on a 20-scenario subset and asserts that batched execution is ≥ 15% faster than serial.

- [ ] **T024c** depends_on: [T009, T010] Implement vectorized statistical operations in `stats_models.py` and `sensitivity.py` to replace Python loops with numpy/pandas vectorized operations. **Specific implementation requirement**: Use `numpy.polyfit()` for polynomial fitting, `scipy.optimize.curve_fit()` for non-linear regression, and `pandas.groupby().transform()` for group-wise operations. Pre-allocate coefficient arrays (e.g., `slopes = numpy.zeros(n_sweeps)`) instead of appending to lists. Eliminate explicit Python loops over large arrays; loops over metadata or configuration parameters are acceptable.  
  *Path*: `code/analysis/stats_models.py`, `code/analysis/sensitivity.py`  
  *Verification*: Code inspection confirms the use of `numpy.polyfit()`, `scipy.optimize.curve_fit()`, and `pandas.groupby().transform()` with pre-allocated arrays. A unit test (`tests/unit/test_vectorized_stats.py`) asserts that the vectorized implementation produces identical results to a reference serial implementation and completes in < 50% of the serial time on a synthetic dataset of 1000 data points.

- [ ] **T024d** depends_on: [T011] Implement in-memory result caching in `comparative_report.py` to avoid redundant disk reads and aggregations. **Specific implementation requirement**: Load `evaluation_results.csv` and `acoustic_results.csv` once into DataFrames at module initialization and cache them in module-level variables (or a class attribute). Reuse the cached DataFrames across all downstream computations (AUC calculation, interaction ANOVA, figure generation). The caching must not introduce state dependencies between test runs (ensure cache is cleared or isolated per invocation).  
  *Path*: `code/analysis/comparative_report.py`  
  *Verification*: Code inspection confirms module-level or class-level caching of loaded DataFrames (e.g., `_CACHE = {}` at module top, populated on first load). A unit test (`tests/unit/test_cached_io.py`) verifies that the second call to a cached aggregation function completes in < 10% of the time of the first call, confirming cache hits.

- [ ] **T024e** depends_on: [T024a, T024b, T024c, T024d] Integration test that validates the optimized pipeline completes the full dataset analysis within the 6-hour constraint on a CPU-only runner. **Requirement**: Execute the full pipeline (T004 through T012, T018–T020) on all 213 scenarios × 10 latency conditions and measure total wall-clock time, CPU usage, and peak memory. Assert that total runtime ≤ 21600 seconds (6 hours) and peak RAM ≤ 7168 MB (7 GB). Write results to `data/analysis/optimization_report.json` with fields `total_runtime_seconds`, `peak_memory_mb`, `cpu_usage_percent`, `scenarios_processed`, `constraint_satisfied` (boolean). If constraints are violated, the task fails with a detailed report of bottlenecks.  
  *Path*: `code/analysis/optimization_report.py`  
  *Verification*: The JSON file contains all required fields. A CI job (`tests/integration/test_optimization_integration.py`) runs the full pipeline on a simulated CPU-only runner and asserts `constraint_satisfied == true`. If the constraint is violated, the job exits with non-zero status, blocking pipeline advancement.

---

## Phase 6 – Testing, documentation, CI integration & reproducibility

- [ ] **T016** depends_on: [T001, T002, T003, T004, T005, T006, T008, T009, T010, T011, T012, T018, T019, T020, T024a, T024b, T024c, T024d, T024e] Verify CPU-only execution by asserting that no GPU libraries are imported and `torch.cuda.is_available()` returns False during pipeline execution. Create a test script `code/tests/unit/test_cpu_only.py` that runs the full pipeline and checks for GPU usage.  
  *Path*: `code/tests/unit/test_cpu_only.py`  
  *Verification*: The test exits with status 0 only if no CUDA or GPU-specific libraries are detected; if any GPU library is imported or torch.cuda.is_available() returns True, the test fails with a clear error message. This directly enforces FR-006.

- [ ] **T017** depends_on: [T004, T005, T006, T008, T009, T010, T011, T012, T018, T019, T020, T024a, T024b, T024c, T024d, T024e] **Blocking verification gate**: Measure and profile the total runtime of the full-dataset pipeline (all 213 scenarios × 10 latency steps). Record wall-clock time, CPU usage, and peak memory usage. Assert that total runtime ≤ 6 hours and peak RAM usage ≤ 7 GB on a CPU-only GitHub Actions runner. This is a **blocking gate**: if either constraint is violated, the task fails the entire CI run. Write results to `data/analysis/runtime_profile.json`.  
  *Path*: `code/analysis/runtime_profiler.py`  
  *Verification*: The JSON file contains fields `total_runtime_seconds`, `peak_memory_mb`, `cpu_usage_percent`, and `constraint_satisfied` (boolean). The script exits with **non-zero status** (failing CI) if total_runtime > 21600 seconds (6 hours) OR peak_memory > 7168 MB (7 GB). If constraints are satisfied, the script exits with status 0. This verification directly enforces SC-004 and FR-007 by blocking pipeline advancement if the 6-hour or 7 GB constraints are violated.

- [ ] **T025** depends_on: [T017] Implement GitHub Actions workflow configuration (`.github/workflows/blocking-gate.yml`) that wires T017 (runtime_profiler.py) into the CI pipeline as a blocking gate. **Requirement**: The workflow must (a) run after all implementation tasks complete (T001–T024e), (b) invoke `python code/analysis/runtime_profiler.py`, (c) check the exit status and the `constraint_satisfied` field in the output JSON, and (d) fail the entire workflow (exit non-zero) if either the script exits with non-zero status OR `constraint_satisfied == false`. The workflow must publish the runtime_profile.json as an artifact for review.  
  *Path*: `.github/workflows/blocking-gate.yml`  
  *Verification*: The workflow file exists and is valid YAML. A CI run that violates the 6-hour or 7 GB constraint exits with a non-zero status, blocking the workflow. A CI run that satisfies the constraints completes successfully. The runtime_profile.json is published as a build artifact.

- [ ] **T021** depends_on: [T004, T005, T006, T008, T009, T010, T011, T012, T016, T017, T018, T019, T020, T024a, T024b, T024c, T024d, T024e, T025] Write a comprehensive integration test that runs the full pipeline from dataset download to comparative report on a **sample** of 5 scenarios (to keep CI time short). The test must assert that (a) all intermediate CSV/JSON files are produced, (b) the final report contains a non‑null `knee_point_ms`, and (c) total runtime on the CI runner is < 30 minutes.  
  *Path*: `tests/integration/test_end_to_end.py`  
  *Verification*: CI executes `pytest -k test_end_to_end`; the test passes and prints the path of the generated report.

- [ ] **T022** depends_on: [T004, T005, T006, T008, T009, T010, T011, T012, T016, T017, T018, T019, T020, T024a, T024b, T024c, T024d, T024e, T025] Update `quickstart.md` with a single reproducible command that a reviewer can run on a fresh clone to reproduce the end‑to‑end study (e.g., `bash run_all.sh`). The command must internally invoke the scripts from T004‑T020 and T024 in the correct order.  
  *Path*: `quickstart.md`  
  *Verification*: Running the command on a clean runner completes without manual intervention and ends with "✅ Study completed – report at `data/report/comparative_report.json`".

- [ ] **T023** depends_on: [T004, T005, T006, T008, T009, T010, T011, T012, T016, T017, T018, T019, T020, T024a, T024b, T024c, T024d, T024e, T025] Add a `README.md` section that documents (i) the random‑seed values used, (ii) the exact EVA‑Bench version/repo URL, (iii) the hardware constraints (CPU‑only, ≤ 7 GB RAM, ≤ 6 h), and (iv) how to reproduce the statistical analyses (command‑line flags).  
  *Path*: `README.md` (appendix)  
  *Verification*: Manual inspection confirms the presence of all four bullet points; the CI runs `grep` checks that each keyword appears.

---

### Execution Graph

The tasks are organized into phases with explicit `depends_on` annotations to enforce the data-flow and logical ordering. **Both the prose description below and the task-level `depends_on` tags in each task header must be satisfied to enforce the dependency graph.**

1. **Phase 1 (T001–T003)**: Project scaffolding. T001, T002, T003 are parallel-safe and have no inter-dependencies.
2. **Phase 2 (T004–T005)**: Data acquisition. T004 depends on T001–T003; T005 depends on T004.
3. **Phase 3 (T006, T008)**: Latency injection & evaluation. T006 depends on T005; T008 depends on T006. **T008 must produce `agent_response_text`, `task_success`, and `turn_boundaries` fields for downstream behavioral-metrics extraction (T018).**
4. **Phase 4 (T009, T010)**: Statistical analysis. T009 depends on T008; T010 depends on T009.
5. **Phase 5 (T011, T012, T018, T019, T020)**: Comparative reporting & behavioral metrics. T011 depends on T008 (not T009–T010); T012 depends on T011; T018 depends on T008 and requires T008 output fields; T019 depends on T005; T020 depends on T005. **T009–T010 (sensitivity analysis) and T011 (comparative report) are independent: T011 consumes only T008 results and the pre-existing acoustic baseline, not T009–T010. Both can run in parallel after T008 completes.**
6. **Phase 5.5 (T024a–T024e)**: Pipeline optimization. T024a modifies T006; T024b modifies T008; T024c modifies T009–T010; T024d modifies T011. T024e is an integration test that depends on all optimizations (T024a–T024d). All optimization tasks are prerequisites for T017 (runtime verification).
7. **Phase 6 (T016, T017, T025, T021, T022, T023)**: Testing, documentation, CI integration & reproducibility. T016 and T017 depend on all implementation and optimization tasks (T001–T024e); T025 (CI workflow) depends on T017; T021 depends on all implementation and T025; T022 and T023 depend on all implementation tasks.

### Dependency ordering (detailed)

| Phase | Tasks | Upstream Dependencies | Notes |
|-------|-------|----------------------|-------|
| 1 | T001, T002, T003 | None | Parallel-safe; no inter-dependencies. |
| 2 | T004 | T001, T002, T003 | Dataset download; depends on scaffolding. |
| 2 | T005 | T004 | Dataset validation; consumes T004 output. |
| 3 | T006 | T005 | Latency injection; consumes validated dataset. Streaming chunks. |
| 3 | T008 | T006 | Pipeline runner; consumes injected audio from T006. Produces required fields for T018. |
| 4 | T009 | T008 | Statistical analysis (ANOVA, piecewise regression); consumes T008 results. Vectorized operations. |
| 4 | T010 | T009 | Sensitivity analysis; refines T009 knee point. Vectorized operations. |
| 5 | T011 | T008 | Comparative report; consumes T008 results and pre-existing baseline. Independent of T009–T010. Cached I/O. |
| 5 | T012 | T011 | Visualization; consumes T011 report. |
| 5 | T018 | T008 | Behavioral metrics; consumes T008 evaluation results (agent_response_text, task_success, turn_boundaries). Implements independence validation. |
| 5 | T019 | T005 | Injection config validation; depends on dataset validation. |
| 5 | T020 | T005 | Perturbation profile validation; depends on dataset validation. |
| 5.5 | T024a | T006 | Streaming audio optimization; modifies latency_injector.py. |
| 5.5 | T024b | T008 | Batched execution optimization; modifies pipeline_runner.py. |
| 5.5 | T024c | T009, T010 | Vectorized stats optimization; modifies stats_models.py and sensitivity.py. |
| 5.5 | T024d | T011 | Cached I/O optimization; modifies comparative_report.py. |
| 5.5 | T024e | T024a, T024b, T024c, T024d | Integration test for optimization; validates 6-hour and 7 GB constraints. |
| 6 | T016 | T001–T012, T018–T020, T024a–T024e | CPU-only verification; depends on all implementation and optimization tasks. |
| 6 | T017 | T001–T012, T018–T020, T024a–T024e | Runtime profiling & blocking gate; depends on all implementation and optimization tasks. Fails CI if constraints violated. |
| 6 | T025 | T017 | GitHub Actions blocking-gate workflow; wires T017 into CI pipeline. |
| 6 | T021 | T001–T012, T016, T017, T018–T020, T024a–T024e, T025 | Integration test; full pipeline on 5-scenario sample. |
| 6 | T022 | T001–T012, T016, T017, T018–T020, T024a–T024e, T025 | Quickstart documentation; depends on complete working code. |
| 6 | T023 | T001–T012, T016, T017, T018–T020, T024a–T024e, T025 | README documentation; depends on complete working code. |

All tasks marked `[P]` can be executed in parallel where their file paths do not overlap. Tasks without `[P]` are sequential. The `depends_on` annotations in each task header are the authoritative source for dependency resolution; the prose table above is a summary for human readability.