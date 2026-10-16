# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Inputs**: `spec.md`, `plan.md`, current research artifacts, and reviewer feedback.  
**Research question**: Does LLM-generated code exhibit statistically significant differences in structural testability metrics compared to human-written code on HumanEval?

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] Implement reproducible data acquisition and human reference extraction in `code/download_data.py` and `code/extract_human_reference.py`
  - Download HumanEval via `datasets.load_dataset("openai/openai_humaneval", revision=<pinned commit hash>)`, save to `data/raw/humaneval.parquet`, compute SHA256 with `code/utils/hash_utils.py`, and record `checksum`, `commit_hash`, `download_date` in `data/raw/metadata.yaml` (FR-001). A checksum mismatch or failed fetch MUST raise `RuntimeError` — never fall back to synthetic data.
  - Extract `canonical_solution` per task into `data/generated/human_samples.json` (JSONL) with fields `task_id`, `code`, `source="human"`, validating against `specs/.../contracts/human_samples.schema.yaml`.
  - Include `code/utils/seeds.py` pinning `random`/`numpy`/`torch` seeds imported first by all scripts (FR-001, Principle I), and `code/utils/logger.py` emitting ISO-8601 timestamps and `task_id` (FR-007).
  - **Verification**: running `python code/download_data.py && python code/extract_human_reference.py` produces both files; the parquet hash matches `metadata.yaml`; every JSONL line passes schema validation; unit tests in `code/tests/test_hash_utils.py` and `code/tests/test_seeds.py` pass.

- [ ] T002 [US1] Implement primary-model code generation with retry and error logging in `code/generate_code.py`
  - Load `Salesforce/codegen-mono-350M` on `device="cpu"` (deterministic CPU‑feasible primary model). Attempt the 4B 8‑bit variant first; on OOM automatically fall back to the 350M model.
  - Generate code for all HumanEval tasks with greedy decoding, pinned seeds, exponential‑backoff retry, and a **60‑second per‑task timeout**. Retries continue until a successful generation or until the fallback model succeeds; no task is allowed to finish with `status="failed"`—the script must raise if generation cannot succeed after fallback.
  - Write `data/generated/codegen_samples.json` (JSONL) with `task_id`, `code`, `model`, `status="success"`, `generation_time`, validating against `llm_samples.schema.yaml`. All 164 entries contain non‑empty `code`.
  - Log `generation_duration_ms` and `tasks_per_minute` events for capacity checks (SC-001, SC-002).
  - **Verification**: the JSONL contains exactly one entry per HumanEval task, each with non‑null `code`; a forced‑failure unit test confirms proper error raising.

- [ ] T003 [US1] Implement filtered metrics pipeline in `code/analyze_metrics.py` with sandboxed test execution
  - Load generated samples (human and LLM) and execute each code sample in `code/sandbox.py` (60 s timeout) to compute `pass_rate` (float ratio of passed tests).
  - Filter samples with `pass_rate >= 0.80`. **Only filtered samples proceed to structural analysis**, satisfying FR-005.
  - For each filtered sample, compute:
    - `cyclomatic_complexity` (integer) via `radon`.
    - `static_branch_count` (integer) via `radon`.
    - `dynamic_branch_coverage` (float 0‑1) via `coverage.py`.
    - Retain `pass_rate` (float) for record.
  - Write two files:
    - `data/analysis/analysis.json` conforming to `analysis.schema.yaml` (includes all fields, float `pass_rate`).
    - `data/analysis/metrics.json` conforming to `metrics.schema.yaml` (uses **binary** `pass_rate` field: `1` if `pass_rate >= 0.80`, else `0`; includes required fields `task_id`, `model`, `cyclomatic_complexity`, `static_branch_count`, `dynamic_branch_coverage`, `pass_rate`, `is_valid`, `parse_error`).
  - Record any radon parse failures with `null` for the affected fields and set `parse_error=true` (allowed by `analysis.schema.yaml`).
  - **Verification**: a known‑passing sample yields `pass_rate == 1.0` in `analysis.json` and `pass_rate == 1` in `metrics.json`; a failing sample is excluded from both files; schema validation tests exist (see T012).

- [ ] T004 [US1] Produce pass‑rate summary for all tasks
  - Run the full pass‑rate evaluation (without structural analysis) on **all** 164 tasks for human and LLM code, writing `data/analysis/pass_rate_summary.json` (list of `task_id`, `source_type`, `pass_rate`).
  - **Verification**: counts match 164 per source; values are floats between 0 and 1; schema‑agnostic sanity checks pass.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] Implement paired Wilcoxon analysis, Kolmogorov‑Smirnov test, MDES, and bias analysis in `code/stats_analysis.py`
  - Pair human vs. codegen metrics from `metrics.json` (filtered set) by `task_id`.
  - Perform two‑tailed Wilcoxon Signed‑Rank tests (α = 0.05) on `cyclomatic_complexity`, `static_branch_count`, and `dynamic_branch_coverage`.
  - Perform a Kolmogorov‑Smirnov test on the distribution of `cyclomatic_complexity` (filtered set) and record `ks_statistic` and `ks_p_value`.
  - Compute Minimum Detectable Effect Size (MDES) for N = 164, α = 0.05, power = 0.80; also compute achieved post‑hoc power and 95 % CI for observed effect sizes (FR‑008, SC‑005).
  - Conduct Little’s MCAR test on prompt length versus inclusion status, reporting `bias_analysis.mcar_test_p_value` and `difficulty_comparison` (means and p‑value).
  - Write `data/analysis/statistical_results.json` conforming to `statistical_results.schema.yaml` (includes Wilcoxon, KS, MDES, power, bias fields).
  - **Verification**: unit tests in `code/tests/test_statistics.py` reproduce known Wilcoxon, KS, and MDES values; schema validation via T019.

- [ ] T006 [US2] Run CodeLlama sensitivity analysis and extend statistical results
  - Load quantized GGUF model `TheBloke/CodeLlama-3B-Instruct-GGUF` via `llama-cpp-python` (CPU, `n_ctx=2048`).
  - Generate code for all tasks, writing `data/generated/sensitivity_samples.json` (validated against `llm_samples.schema.yaml`).
  - Re‑run the filtered metrics pipeline on sensitivity samples, merging results into `analysis.json` with `model="codellama-3b"` and updating `metrics.json` accordingly.
  - Perform Levene’s test on each metric between the primary (codegen‑mono) and sensitivity (CodeLlama) models; record `levene_statistic`, `levene_p_value`, and a boolean `variance_exceeds_threshold` (true if variance difference > 0.05) in `statistical_results.json`. Propagate the KS fields from T005 to keep the schema satisfied.
  - **Verification**: sensitivity JSONL has 164 entries; Levene fields are present; KS fields persist; unit tests in `code/tests/test_sensitivity.py` validate calculations.

- [ ] T007 [US1] Add independent correctness, sensitivity, and runtime checks
  - Add `code/tests/test_metrics_schema.py` to validate `analysis.json` against `analysis.schema.yaml` and `metrics.json` against `metrics.schema.yaml`.
  - Add `code/tests/test_stats_pipeline.py` for end‑to‑end integration (metrics → statistical_results).
  - Add `code/tests/test_coverage_distinction.py` confirming static vs. dynamic branch metrics differ on a crafted example.
  - Aggregate generation and execution logs into `data/analysis/performance.json` (measured `generation_duration_ms`, `tasks_per_minute`, total runtime) and compare against the 6‑hour capacity goal (SC‑001, SC‑002, SC‑003).
  - **Verification**: all tests pass; `performance.json` contains numeric values; summary records pass/fail per check with no invented numbers.

- [ ] T008 [US3] Generate figures and the Markdown report from validated outputs in `code/report_generator.py`
  - Produce histograms and box plots (PNG) under `figures/` comparing human vs. LLM metrics for both the filtered set and the full pass‑rate summary.
  - Render `paper/report.md` programmatically from `analysis.json`, `metrics.json`, `statistical_results.json`, and `power_results.yaml`; embed MDES, achieved power, CIs, Levene results, KS results, and bias analysis. All numbers are pulled directly from the JSON/YAML files (no hand‑typed values).
  - Validate every citation in the report via the Reference‑Validator Agent; remove any citation that fails validation.
  - **Verification**: every figure referenced exists; the MDES value in the report matches `statistical_results.json`; citation validation passes.

- [ ] T009 [US3] Track artifact integrity for all analysis outputs
  - Compute SHA256 hashes for every file under `data/analysis/` (including `analysis.json`, `metrics.json`, `statistical_results.json`, `power_results.yaml`, `artifact_hashes.yaml`) and write `data/analysis/artifact_hashes.yaml` conforming to `artifact-hashes.schema.yaml`.
  - **Note**: Updating the project‑level state file `state/projects/PROJ-294-evaluating-the-impact-of-code-generation.yaml` is handled by the platform; this task does not write to `state/` as prohibited by task rules.
  - **Verification**: schema validation succeeds; recomputed hashes match stored values.

- [ ] T010 Write the methods/results account and paper‑stage handoff
  - Write `paper/methods_and_results.md` summarizing the pipeline, pinned dataset revision, model versions, statistical outcomes (including negative findings), and limitations. Link each referenced artifact with its SHA256 hash from `artifact_hashes.yaml`.
  - **Verification**: all referenced artifact paths exist; hashes resolve correctly; values match those in `statistical_results.json`.

- [ ] T011 Re‑run the documented workflow end‑to‑end and confirm reproducibility
  - Document the full run command sequence in `quickstart.md` (download → extract → generate → metrics → stats → sensitivity → report → hashes) and re‑execute it on a fresh runner.
  - **Verification**: a fresh run reproduces identical `analysis.json`, `metrics.json`, and `statistical_results.json` (given pinned seeds and revisions); all unit tests pass; report files are present and parseable.

## Phase 3: Contract validation suite (new)

- [ ] T012 Add comprehensive contract validation tests
  - Implement `code/tests/test_contracts.py` that programmatically validates:
    - `analysis.json` against `analysis.schema.yaml`
    - `artifact_hashes.yaml` against `artifact-hashes.schema.yaml`
    - `data/raw/humaneval.parquet` against `dataset.schema.yaml`
    - Processed dataset files against `dataset_schema.schema.yaml`
    - `human_samples.json` against `human_samples.schema.yaml`
    - `codegen_samples.json` and `sensitivity_samples.json` against `llm_samples.schema.yaml`
    - `metrics.json` against `metrics.schema.yaml`
    - Dummy `metrics_alt.json` against `metrics_schema.schema.yaml` (includes `mutation_score`)
    - `statistical_results.json` against `statistical_results.schema.yaml`
    - `power_results.yaml` against `power.schema.yaml`
    - `validation_results.yaml` against `validation_results.schema.yaml`
  - **Verification**: all schema validations succeed; failures abort the CI.

- [ ] T013 Generate dummy `metrics_alt.json` to satisfy the orphan `metrics_schema.schema.yaml`
  - Produce a minimal JSON file containing required fields (`task_id`, `model`, `cyclomatic_complexity`, `static_branch_count`, `dynamic_branch_coverage`, `pass_rate`, `is_valid`, `parse_error`, `mutation_score`) with placeholder values for demonstration purposes only.
  - **Verification**: file validates against `metrics_schema.schema.yaml`.

- [ ] T014 Generate `validation_results.yaml` aggregating validation outcomes
  - Summarize results of Wilcoxon test, power analysis, KS test, Levene test, and citation validation per `validation_results.schema.yaml`.
  - **Verification**: file conforms to its schema; values match those computed earlier.

## Phase 4: Constitution‑level hash tracking (flagged for kickback)

- [ ] T015 (plan‑root cause) Record SHA256 hashes of all `data/` artifacts in the project‑level state file `state/projects/PROJ-294-evaluating-the-impact-of-code-generation.yaml` as required by Constitution Principle III & V.  
  *Note*: This task cannot be implemented directly by project scripts (writes to `state/` are prohibited). The requirement is flagged for architectural kick‑back to the platform team.

- [ ] T016 Generate `validation_results.yaml` aggregating validation outcomes and validate against its schema
  - After completing the statistical analysis and report generation, compile a YAML file `validation_results.yaml` in `data/analysis/` that includes:
    - Wilcoxon test statistic and p‑value per metric
    - Kolmogorov‑Smirnov test statistic and p‑value
    - MDES and achieved power
    - Levene’s test statistic and p‑value
    - Citation validation boolean
  - Validate this file against `validation_results.schema.yaml` using `jsonschema`.
  - **Verification**: schema validation passes; the file is included in `artifact_hashes.yaml` tracking.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001 (Download & Verify) | T001 | `python code/download_data.py` |
| FR-002 (Generation, retry, timeout) | T002 | `python code/generate_code.py` |
| FR-003 (Radon metrics) | T003 | `python code/analyze_metrics.py` |
| FR-004 (Wilcoxon paired, α=0.05) | T005 | `python code/stats_analysis.py` |
| FR-005 (Test execution, pass_rate filter, coverage) | T003, T004 | `pytest code/tests/test_coverage_distinction.py` |
| FR-006 (Report + figures) | T008 | `python code/report_generator.py` |
| FR-007 (Logging) | T001 | logger unit check |
| FR-008 (MDES) | T005 | `statistical_results.json` keys |
| FR-009 (Sensitivity) | T006 | `python code/generate_code_llama.py` |
| FR-010 (Citation validation) | T008 | report citation check |
| FR-011 (Artifact hashes) | T009 | `python code/report_generator.py --hashes` |
| SC-001/002/003 | T002, T007 | `data/analysis/performance.json`, `pass_rate` in analysis |
| SC-005/006 | T005, T006 | `mdes`, `levene_*` in `statistical_results.json` |
| SC-004 | — | Out of scope, documented in report limitations (per plan) |

**Execution order**: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016. T009 can run in parallel with T010 after T008.
