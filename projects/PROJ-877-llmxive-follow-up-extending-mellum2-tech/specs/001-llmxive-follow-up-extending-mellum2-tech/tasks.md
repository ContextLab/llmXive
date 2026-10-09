---
description: "Task list for llmXive follow‑up: extending “Mellum2 Technical Report”"
---

# Tasks: llmXive follow‑up: extending “Mellum2 Technical Report”

**Input**: Design documents from `specs/001-llmxive-complexity-loss/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

**Tests**: Unit‑ and integration‑tests are included for each user story as indicated.  

**Organization**: Tasks are grouped by phase and by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Initialize repository structure and core config files  
  *Create `code/`, `data/`, `tests/`, `docs/`, `.gitignore`, `README.md`, `.env.template`, `ruff.toml`, `pyproject.toml`, `requirements.txt`, `.github/workflows/ci.yml`.*  

- [ ] T002 Add pinned `requirements.txt` (datasets, transformers, tree‑sitter, codeql, scikit‑learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm, pwlf, ruptures, python‑dotenv, joblib, tqdm).  

- [ ] T003 Configure linting/formatting (ruff & black) and concrete CI workflow file `.github/workflows/ci.yml` that runs lint and tests on push.  

- [ ] T004 Create `code/__init__.py` entry point and ensure it is importable.  

- [ ] T078 Verify repository structure and core files exist (`code/`, `data/`, `tests/`, `docs/`, `.gitignore`, `README.md`, `.env.template`, `ruff.toml`, `pyproject.toml`, `requirements.txt`, `.github/workflows/ci.yml`).  

- [ ] T079 Verify `requirements.txt` can be installed (`pip install -r requirements.txt`) without errors.  

- [ ] T080 Verify CI workflow runs lint (`ruff check .`) and passes.  

- [ ] T081 Verify `code/__init__.py` is importable (`python -c "import code"`).  

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T005 [P] Implement configuration loader `code/config.py` (dotenv, required env vars, **fixed random seed** `SEED=12345`, record seed in config file).  

- [ ] T082 Verify config loader reads env vars and that the fixed seed is set and persisted.  

- [ ] T006 [P] Implement generic retry/timeout utilities `code/utils/retry.py` (exponential back‑off, max 3 attempts).  

- [ ] T083 Verify retry utilities respect exponential‑backoff and max‑attempt limit.  

- [ ] T007 Create data‑contract schemas in `code/contracts/`  
  *`code_chunk.schema.yaml`, `correlation_result.schema.yaml`, `threshold_result.schema.yaml`, `analysis_result.schema.yaml`.*  

- [ ] T084 Verify all schema files conform to JSON‑Schema using `jsonschema`.  

- [ ] T008 Implement structured logging `code/logging.py` (JSON lines, level control, thread‑safe queue).  

- [ ] T085 Verify logging emits correctly formatted JSON lines and is thread‑safe.  

- [ ] T009 Add helper for deterministic hashing of artifacts `code/utils/hash.py`.  

- [ ] T086 Verify deterministic hashing produces identical hashes for identical inputs and different hashes for different inputs.  

- [ ] **T036 Optimize inference memory usage `code/inference/memory_opt.py`**  
  *Applies `torch.no_grad()`, half‑precision where safe, and limits thread‑pool size; target memory usage < 5 GB.*  

- [ ] T106 Verify inference memory consumption stays within acceptable memory limits (measured via `psutil`).  

## Phase 3: User Story 1 – Correlation Analysis of Code Complexity and Prediction Loss (Priority P1)

**Goal**: Download code, label with static analysis, run frozen LLM inference, compute correlations, and generate visualisations.  

### Tests (must be written first and fail)

- [ ] T010 [P] `tests/unit/test_download.py::test_download_handles_network_failure`  
- [ ] T011 [P] `tests/unit/test_static_analysis.py::test_skips_unparseable_file`  
- [ ] T012 [P] `tests/unit/test_inference.py::test_timeout_and_retry_logic`  

### Implementation

- [ ] T013 [US1] Implement feasibility & power analysis `code/analysis/feasibility.py`  
  *Streams 50 metadata samples from `codeparrot/github-code`, estimates required N (effect size r≈0.3, α=0.05, power 0.8), writes `data/results/feasibility_report.json`.*  

- [ ] T087 Verify feasibility_report.json exists and matches schema.  

- [ ] T014 [US1] Implement dataset download `code/data/download.py`  
  *Reads `feasibility_report.json`, streams `codeparrot/github-code` (Python + Java) to `data/raw/python/` and `data/raw/java/`, exact `N` samples, fails loudly on fetch errors, generates SHA‑256 checksums recorded in `data/checksums.txt`.*  

- [ ] T088 Verify downloaded shards match recorded SHA‑256 checksums and the expected number of samples.  

- [ ] T015 [US1] Implement static analysis `code/data/static_analysis.py`  
  *Runs CodeQL + tree‑sitter on each file, emits `data/processed/annotated_python.jsonl` and `data/processed/annotated_java.jsonl` with fields `chunk_id`, `cyclomatic_complexity`, `nesting_depth`, `repetition_ratio`.*  

- [ ] T089 Verify static analysis output contains required fields for every chunk.  

- [ ] T016 [US1] Implement variance check `code/analysis/variance_check.py`  
  *Detects zero variance in any metric; if found writes `data/results/variance_null_report.json` and exits with non‑zero code to halt downstream tasks.*  

- [ ] T090 Verify variance check exits with non‑zero status on zero‑variance data.  

- [ ] T017 [US1] Build KenLM n‑gram models `code/data/ngram_builder.py`  
  *Creates `data/models/kenlm_python.arpa` and `data/models/kenlm_java.arpa` from the respective training splits.*  

- [ ] T091 Verify KenLM `.arpa` files can be loaded by `kenlm`.  

- [ ] T018 [US1] Implement LLM inference engine `code/inference/engine.py`  
  *Loads `mistralai/Mistral-7B-Instruct-v0.1` on CPU (`device="cpu"`), processes each annotated chunk, records per‑token loss & entropy, normalises loss using the corresponding KenLM log‑probability (`normalized_loss = loss_nats - ngram_logprob_nats`), respects 60 s per‑chunk limit, retries up to 3 times, writes `data/results/inference_python.jsonl` & `data/results/inference_java.jsonl`.*  

- [ ] T092 Verify inference respects the short‑duration limit per chunk and retries on simulated failure.  

- [ ] T019 [US1] Compute correlations `code/analysis/correlation.py`  
  *Merges annotation and inference results, calculates Pearson & Spearman coefficients for each metric vs. normalized loss, writes `data/results/correlation_stats.json`.*  

- [ ] T093 Verify `correlation_stats.json` contains both Pearson and Spearman keys with numeric values.  

- [ ] T020 [US1] Generate visualisations `code/viz/plots.py`  
  *Creates scatter plots with regression lines for each metric/language, saves PNGs under `data/figures/`, updates `correlation_stats.json` with plot paths.*  

- [ ] T094 Verify PNG files are created and referenced in `correlation_stats.json`.  

- [ ] T021 [US1] Cross‑language validation `code/analysis/cross_language.py`  
  *Compares Python vs. Java correlation coefficients, adds `cross_lang_comparison` section to `correlation_stats.json`.*  

- [ ] T095 Verify `cross_lang_comparison` section exists with language‑specific coefficients.  

## Phase 4: User Story 2 – Non‑Linear Threshold Detection (Priority P2)

**Goal**: Detect structural breakpoints where the complexity‑loss relationship changes and assess their stability.  

### Tests

- [ ] T022 [P] `tests/unit/test_threshold.py::test_piecewise_detects_breakpoint`  
- [ ] T023 [P] `tests/unit/test_threshold.py::test_linear_data_returns_no_breakpoint`  

### Implementation

- [ ] T048 [US2] Compute correlations for threshold detection `code/analysis/correlation_us2.py`  
  *Same as T019 but outputs `data/results/correlation_us2.json` for use by US‑2 only.*  

- [ ] T087 Verify `correlation_us2.json` contains Pearson and Spearman coefficients.  

- [ ] T024 [US2] Implement change‑point detection `code/analysis/threshold.py`  
  *Uses `ruptures` (PELT) on the appropriate correlation_us dataset, outputs candidate breakpoints to `data/results/threshold_candidates.json`.*  

- [ ] T096 Verify `threshold_candidates.json` includes a `candidate_breakpoints` array.  

- [ ] T025 [US2] Model comparison & selection `code/analysis/threshold.py` (extended)  
  *Computes AIC/BIC for linear vs. piecewise models, adds `model_preference` field (`linear` or `piecewise`).*  

- [ ] T097 Verify `model_preference` is correctly set based on AIC/BIC thresholds.  

- [ ] T037 Parallelise bootstrap resampling `code/analysis/threshold_sensitivity_parallel.py` (uses `joblib.Parallel`).  

- [ ] T107 Verify `joblib.Parallel` is used and a speedup > 1.5× over serial execution is observed.  

- [ ] T026 [US2] Sensitivity analysis `code/analysis/threshold_sensitivity.py`  
  *Reads `perturbation_magnitudes` from `feasibility_report.json`, perturbs the complexity metric by each magnitude, re‑runs threshold detection, performs `bootstrap_count` resamples, records `threshold_shifts_by_magnitude` and overall `stability_status` (pass if max shift ≤ 0.05). Writes `data/results/threshold_sensitivity.json`.*  

- [ ] T098 Verify `threshold_sensitivity.json` follows the required structure and respects the ≤ 0.05 stability rule.  

- [ ] T027 [US2] Produce markdown report `code/report/threshold_report.md`  
  *Summarises identified thresholds, model preference, sensitivity table, and justification.*  

- [ ] T099 Verify `threshold_report.md` exists and contains required sections (breakpoints, justification, stability).  

## Phase 5: User Story 3 – Statistical Significance and Power Validation (Priority P3)

**Goal**: Verify that observed correlations and thresholds are not due to chance and assess study power.  

### Tests

- [ ] T028 [P] `tests/unit/test_permutation.py::test_permutation_shuffles_correctly`  
- [ ] T029 [P] `tests/unit/test_correction.py::test_bonferroni_adjustment`  

### Implementation

- [ ] T049 Prepare data for permutation tests `code/analysis/prepare_permutation.py`  
  *Merges annotation and inference results (independent of US‑1/US‑2 outputs) into `data/results/merged_for_permutation.jsonl`.*  

- [ ] T087 Verify `merged_for_permutation.jsonl` exists and matches schema.  

- [ ] T030 [US3] Cluster‑robust permutation test `code/analysis/permutation_test.py`  
  *Performs block permutations at repository level on the merged dataset, computes empirical p‑value, writes `data/results/permutation_pvalue.json`.*  

- [ ] T100 Verify `permutation_pvalue.json` contains an empirical p‑value and the configured permutation count (e.g., 1000).  

- [ ] T031 [US3] Multiple‑comparison correction `code/analysis/multicomp_correction.py`  
  *Applies Bonferroni and Benjamini‑Hochberg FDR to all p‑values from T030, writes `data/results/corrected_pvalues.json`.*  

- [ ] T101 Verify `corrected_pvalues.json` contains adjusted p‑values for all hypotheses.  

- [ ] T032 [US3] Benchmark validation `code/analysis/benchmark_validation.py`  
  *Attempts to load the CodeXGLUE complexity benchmark from HuggingFace, if available computes Pearson correlation with our computed metrics and writes `data/results/benchmark_validation.json` (`status: validated`). If unavailable, writes `data/results/benchmark_limitation_report.md` and a JSON with `status: limitation_report_generated`.*  

- [ ] T102 Verify either `benchmark_validation.json` or `benchmark_limitation_report.md` exists and that the `status` field matches the generated artifact.  

- [ ] T033 [US3] Power‑sensitivity reporting `code/report/power_report.md`  
  *Summarises the a‑priori power analysis (from T013), the observed effect size, and any limitations.*  

- [ ] T103 Verify `power_report.md` contains sections for a‑priori analysis, observed effect size, and limitations.  

## Phase N: Polish & Cross‑Cutting Concerns (split into atomic phases)

### Documentation & Presentation

- [ ] T034 Update `README.md` with full usage instructions, pipeline diagram, and interpretation of results.  

- [ ] T104 Verify `README.md` contains usage section, a DAG diagram, and an interpretation summary.  

- [ ] T035 Generate API reference `docs/api.md` listing public functions in `code/` modules.  

- [ ] T105 Verify `docs/api.md` lists all public functions.  

### Optimization & Parallelisation

- [ ] T036 (already placed before inference) – see Phase 2.  

- [ ] T037 (already placed before sensitivity) – see Phase 4.  

### Testing & Validation

- [ ] T108 Integration test: end‑to‑end pipeline success on a small sample dataset.  

- [ ] T109 Integration test: network failure handling during download.  

- [ ] T110 Integration test: zero‑variance dataset handling.  

- [ ] T111 Verify DAG definition `code/dag.yaml` loads, contains all task IDs, and is acyclic.  

- [ ] T112 Verify quick‑start script (`scripts/quick_start.sh`) runs the full pipeline without errors and produces a success log.  

### Runtime & Data Integrity

- [ ] T041 Wrap full pipeline execution, measure total runtime, and assert it is ≤ 6 hours; write `data/results/runtime_report.json`.  

- [ ] T079 Verify recorded runtime ≤ 21600 seconds.  

- [ ] **T043 Generate SHA‑256 checksums for every raw and derived data file, store in `data/checksums.txt`, and verify integrity before each downstream task.**  

- [ ] T078b Verify checksum file exists and all listed hashes match actual files.  

## Phase N – Finalisation

- [ ] T076 Verify README update (T034) was performed and contains required sections.  

- [ ] T077 Verify API reference generation (T035) was performed and lists all public functions.  

- [ ] T041 (runtime) and T043 (checksum) are now integral to the pipeline, satisfying SC‑005 and Constitution Principle III.  