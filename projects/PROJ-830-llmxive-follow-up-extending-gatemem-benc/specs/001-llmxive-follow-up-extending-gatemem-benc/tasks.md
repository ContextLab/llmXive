# Tasks: llmXive follow‑up – extending GateMem benchmark  

**Inputs**: `spec.md`, `plan.md`, existing contracts and code skeletons.  
**Goal**: Build a CPU‑tractable gatekeeper pipeline, run it and the two baselines on the real GateMem dataset, compute the three core metrics, profile computational cost, perform statistically‑sound comparisons, and generate a reproducible benchmark report.  

---  

## Completed foundational work  

- [ ] T001 [P] Create the JSON‑Schema contracts (`dataset.schema.yaml`, `evaluation_result.schema.yaml`, `metrics.schema.yaml`, `results.schema.yaml`, `output.schema.yaml`) under `specs/001-llmxive-follow-up-extending-gatemem-benc/contracts/`.  
  *Verification*: `pytest tests/contract/test_dataset_schema.py` and analogous contract tests all pass.  

- [X] T002 [P] Draft `quickstart.md` (in the spec folder) that documents environment setup, dataset download, and the command to run the full benchmark.  
  *Verification*: `tests/unit/test_docs.py::test_quickstart_exists` succeeds and the file contains the required “dataset download” and “run commands” sections.  

- [ ] T003 [P] Implement `src/utils/profiling.py` with `profile_execution(func, *args, **kwargs)` returning `{'latency_ms':…, 'peak_ram_mb':…}` using `psutil`.  
  *Verification*: `tests/unit/test_profiling.py::test_profile_execution_returns_dict` passes.  

---  

## Pending research‑stage tasks  

- [ ] T010 [ ] Implement real‑data loader – `src/utils/data_loader.py`  
  - Stream GateMem via `datasets.load_dataset(..., streaming=True)`.  
  - Validate each episode against `contracts/dataset.schema.yaml`; abort with `ConnectionError` on fetch failure.  
  - Compute SHA‑256 checksums, write to `state/artifact_hashes.yaml`.  
  - Exclude ambiguous `leak_target` episodes, log to `logs/edge_cases.log`.  
  - *Verification*: `tests/unit/test_data_loader.py::test_fetch_streaming` succeeds.  

- [ ] T010a [ ] Validate sentiment‑to‑intent mapping – `src/gatekeeper/classifier.py` & `tests/unit/test_classifier_mapping.py`  
  - Run the DistilBERT classifier on a manually‑labeled subset (~200 episodes).  
  - Compute accuracy of SST‑2 sentiment → intent mapping; require ≥ 80 % accuracy.  
  - Abort with warning if below threshold.  
  - *Verification*: `tests/unit/test_classifier_mapping.py::test_mapping_accuracy` passes.  

- [ ] T011 [ ] Build DistilBERT intent classifier – `src/gatekeeper/classifier.py`  
  - Load `distilbert-base-uncased-finetuned-sst-2-english` on CPU (`device="cpu"`).  
  - Map sentiment labels to intents (`positive→query`, `negative→deletion`, etc.).  
  - One‑retry for cache corruption; on second failure exit 1 with log “Critical: Model Unavailable”.  
  - Return `{intent, inference_time_ms, peak_ram_mb}` using shared profiler.  
  - *Verification*: `tests/unit/test_classifier.py::test_cpu_only_enforcement` passes.  

- [ ] T012 [ ] Implement regex‑based rule engine – `src/gatekeeper/rules.py`  
  - Validate `role` against whitelist in `config.py`.  
  - Parse `deletion_log`; malformed entries default to deny and log to `logs/deletion_errors.log`.  
  - Provide `apply_rules(episode_dict) → bool`.  
  - *Verification*: `tests/unit/test_rules.py::test_malformed_handling` succeeds.  

- [~] T013 [ ] Gatekeeper pipeline – `src/gatekeeper/pipeline.py`  
  - For each streamed episode: run classifier, then rules.  
  - If allowed, invoke LLM backbone (`src/utils/config.py` → `get_llm_singleton()`) with prompts from `templates/prompts.yaml`.  
  - Record results in `data/processed/gatekeeper_results.jsonl` (conforms to `evaluation_result.schema.yaml`).  
  - Profile each episode.  
  - *Verification*: `tests/integration/test_us1_medical_domain.py` produces non‑empty results file with required fields.  

- [ ] T013a [ ] Verify LLM runs on CPU‑only – `tests/unit/test_llm_cpu.py`   <!-- FAILED-IN-EXECUTION: tests/unit/test_llm_cpu.py exit=1 -->
  - Assert `device='cpu'` and successful minimal inference with the 2.7 B int8 Llama‑3 model.  
  - *Verification*: test passes on the CI runner.  

- [ ] T014 [ ] Baseline pipelines – `src/baselines/retrieval.py` & `src/baselines/long_context.py`  
  - Load same LLM instance and prompts.  
  - No gating; query proceeds directly to LLM.  
  - Write results to `data/processed/retrieval_results.jsonl` and `data/processed/long_context_results.jsonl`.  
  - Profile each episode.  
  - *Verification*: schema compliance tests pass.  

- [ ] T015 [ ] Metric computation – `src/metrics/` package  
  - Compute Access Control, Utility (including conditional utility), and Forgetting scores per pipeline/domain.  
  - Write aggregated objects to `data/processed/aggregated_metrics.json` (conforms to `metrics.schema.yaml`).  
  - *Verification*: `tests/unit/test_metrics.py::test_all_metrics_calculation` validates scores in [0, 1].  

- [ ] T016 [ ] Statistical analysis & correction (including power‑analysis episode‑count verification and Holm‑Bonferroni corrected p‑values) – `src/stats/`  
  - Fit logistic GLMM for Access Control and Forgetting; linear mixed‑effects model for Utility.  
  - Perform Shapiro‑Wilk normality checks; fall back to non‑parametric paired tests if needed.  
  - Verify each domain contains ≥ 100 episodes; abort with error if not met (power‑analysis requirement).  
  - Apply Holm‑Bonferroni correction across six primary hypothesis tests (α = 0.0083).  
  - Output `data/processed/statistical_results.json` (conforms to `results.schema.yaml`).  
  - *Verification*: `tests/unit/test_stats.py::test_orchestrate_stats_returns_dict` confirms hierarchy and correction.  

- [ ] T016a [ ] Test Holm‑Bonferroni correction and schema compliance – `tests/unit/test_stats_correction.py`  
  - Load `statistical_results.json`; assert `p_value` fields are Holm‑Bonferroni adjusted and that the file validates against `results.schema.yaml`.  
  - *Verification*: test passes.  

- [ ] T017 [ ] End‑to‑end CLI driver (orchestration) – `src/cli/run_evaluation.py`  
  - Parse `--domains`, invoke gatekeeper and both baselines, then call metric and stats modules.  
  - Generate intermediate artifacts (`unified_metrics.json`, `performance_comparison.json`, `failure_cases.json`).  
  - *Verification*: integration test runs on a tiny subset and produces expected files.  

- [ ] T017b [ ] Generate final benchmark report and package artifacts – `src/cli/generate_report.py`  
  - Format markdown report (`data/results/final_benchmark_report.md`) with tables, p‑values, effect sizes, and cost reductions.  
  - Ensure all required artifacts (metrics, stats, logs, samples) are placed in the final distribution bundle.  
  - *Verification*: `tests/integration/test_report_generation.py` checks report existence and required sections.  

- [ ] T018 [ ] Failure‑case sampling – `src/utils/failure_sampling.py`  
  - Load `unified_metrics.json`; filter false positives/negatives and forgetting violations.  
  - Sample up to 50 cases with seed 42; if > 50, stratify proportionally by `domain`.  
  - Write to `data/samples/failure_cases.json`.  
  - *Verification*: stratified sampling tests pass.  

- [ ] T019 [ ] Robust edge‑case logging – augment `src/utils/data_loader.py` and `src/gatekeeper/rules.py`  
  - Log excluded episodes (ambiguous `leak_target`, missing fields) and rule‑engine deny defaults to `logs/edge_cases.log`.  
  - Include the log in the final artifact bundle.  
  - *Verification*: `tests/unit/test_logging.py::test_edge_case_logging` confirms entries.  

- [ ] T019a [ ] Verify `logs/edge_cases.log` is packaged with final artifact bundle – `tests/unit/test_artifact_packaging.py`  
  - After full run, assert the presence of `logs/edge_cases.log` in the output directory or manifest.  
  - *Verification*: test passes.  

- [ ] T020 [ ] Update quickstart for full benchmark – `specs/001-llmxive-follow-up-extending-gatemem-benc/quickstart.md`  
  - Add “Run full benchmark” command and documentation of report location and Holm‑Bonferroni interpretation.  
  - *Verification*: `tests/unit/test_docs.py::test_quickstart_contains_full_run` succeeds.  

- [ ] T021 [ ] Write final evaluation JSON conforming to `output.schema.yaml` – `data/processed/final_output.json`  
  - Consolidate run metadata, per‑episode results, and aggregated metrics into a single JSON object matching `output.schema.yaml`.  
  - *Verification*: schema validation test passes.  

- [ ] T023 [ ] Run Reference‑Validator Agent on all citation‑containing artifacts before scoring – `src/validation/reference_validator.py`  
  - Invoke the platform’s Reference‑Validator on every markdown, code, and schema file that includes citations.  
  - Halt the pipeline if any citation fails verification.  
  - *Verification*: `tests/unit/test_reference_validator.py` ensures the agent is called and respects failures.  