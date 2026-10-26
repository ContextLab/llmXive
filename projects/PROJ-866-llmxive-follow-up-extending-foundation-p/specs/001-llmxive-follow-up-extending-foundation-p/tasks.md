# Tasks: llmXive follow‑up – extending “Foundation Protocol: A Coordination Layer for Agentic Society”

**Inputs**: `spec.md`, `plan.md`, the data‑model and contracts, and the reviewer feedback calling for a verifiable, deterministic pipeline.

The tasks are organized into research phases.  Each task follows the required checklist format  
`- [ ] T### [P?] [USx?] description … with file path`.  The indented lines list the concrete requirement(s) it satisfies and the verification step(s).

## Phase 1 – Setup, deterministic data generation, and first end‑to‑end run

- [X] T001 [P] **Implement deterministic workflow generator** – `code/services/generator.py` creates `data/raw/workflows.json` containing 500 synthetic workflows that conform to `contracts/workflow.schema.yaml`.  
  - Requirements satisfied: FR‑001, FR‑008, SC‑001, deterministic seed (`SEED=42`).  
  - Verification: after running `python -m code.services.generator --n 500 --seed 42`, the file exists, contains 500 entries, each workflow has a `delegation_depth` between 1‑10 and at least 25 workflows per depth level, and passes JSON‑schema validation.

- [X] T002 [P] **Build independent Oracle Policy Engine** – `code/models/policy.py` provides a pure‑Python `OraclePolicyEngine` that evaluates a workflow against all policy nodes and returns a list of violations.  
  - Requirements satisfied: FR‑008, SC‑001, Constitution VI (independence).  
  - Verification: unit test `tests/unit/test_oracle.py` asserts that a known workflow with a budget‑cap violation yields exactly one violation of type `"budget_exceeded"`.

- [X] T003 [P] **Create tokenizer wrapper** – `code/lib/utils.py` defines `count_tokens(text: str) -> int` using `tiktoken` with model `cl100k_base`.  
  - Requirements satisfied: FR‑009, FR‑004 (consistent token measurement).  
  - Verification: test `tests/unit/test_tokenizer.py` checks that the string `"Hello world"` yields 2 tokens.

- [ ] T004 [P] **Full‑context execution engine** – `code/services/executor_full.py` reads `data/raw/workflows.json`, runs each workflow through the Oracle, tokenizes the entire policy graph, and writes `data/processed/full_context_logs.json` adhering to `contracts/execution_log.schema.yaml` (mode=`full_context`, `compression_depth=0`).
  - Requirements satisfied: FR‑002, FR‑004, FR‑007.  
  - Verification: after `python -m code.services.executor_full --n 5`, the output file exists, contains 5 logs, each log passes schema validation, and token counts are > 0.

- [ ] T005 [P] **Compressed‑context execution engine** – `code/services/executor_compressed.py` implements depth‑limited BFS/DFS extraction (configurable via `--depth K`), uses the tokenizer wrapper, and writes `data/processed/compressed_context_logs.json` (mode=`compressed`).  
  - Handles edge cases:  
    * `compression_depth=0` → `context_reduction_pct="[deferred]"`.  
    * single‑node workflow → `context_reduction_pct="[deferred]"`.  
  - Requirements satisfied: FR‑003, FR‑004, FR‑009, FR‑007.  
  - Verification: run `python -m code.services.executor_compressed --depth 2 --n 5`; the file exists, each entry’s `context_reduction_pct` is a numeric value between 0‑100 (or the string `"[deferred]"` for edge cases), and schema validation succeeds.

- [ ] T006 [P] **Expand execution logs to step‑level outcomes** – `code/utils/step_expander.py` reads both full‑ and compressed logs, creates `data/processed/step_outcomes.json` where each step is a binary record (`outcome` 0/1) together with `context_reduction_pct`, `policy_complexity`, and `delegation_depth`. Rows with `context_reduction_pct="[deferred]"` are flagged but **excluded** from the regression dataset.  
  - Requirements satisfied: FR‑005, new `StepOutcome` model, SC‑001.  
  - Verification: after execution, the JSON file exists, contains > 0 rows, and a separate script confirms that all numeric `context_reduction_pct` rows are ≤ 100 and that rows with the string value are not used in the GEE fit.

- [ ] T007 [P] **Fit binomial GEE regression and produce trade‑off curve** – `code/services/analyzer.py` loads `step_outcomes.json`, fits a binomial GEE (logit link, exchangeable correlation) with covariates `context_reduction_pct`, `policy_complexity`, and `delegation_depth`. It writes:   <!-- FAILED-IN-EXECUTION: code/services/analyzer.py exit=1 -->
  * `data/results/analysis_results.json` (conforms to `contracts/analysis_results.schema.yaml`).  
  * `data/results/tradeoff_curve.csv` (aggregated `compression_ratio`, `error_rate`, `std_dev`, `n_samples`).  
  - Requirements satisfied: FR‑005, FR‑006, SC‑003, SC‑004.  
  - Verification: running `python -m code.services.analyzer` exits 0, both output files exist, JSON validates against its schema, and the CSV contains a column `compression_ratio` ranging from 0‑100 with at least three distinct points. The script also checks that `compression_ratio` equals the numeric `context_reduction_pct` from the source logs.

- [ ] T008 [S] **Multiple‑comparison correction and trend test** – extend `analyzer.py` to compute a Cochran‑Armitage trend test and Bonferroni‑adjusted pairwise p‑values, writing `data/results/multiplicity_tests.json`.  
  - Requirements satisfied: FR‑005, SC‑003, Constitution III (statistical rigor).  
  - Verification: the JSON file contains keys `trend_statistic`, `trend_p_value`, `bonferroni_corrected` (list of dicts with `depth_pair` and `p_value`), and a boolean `significant_at_0.05`.  

- [ ] T009 [P] **Simulation‑based power analysis** – `code/utils/power_analysis.py` simulates 1 000 datasets matching the study design (effect size: logistic coefficient ≈ 0.10 per 10 % reduction). For each dataset it fits the same GEE model and records whether the 1 % error‑threshold is detected at α = 0.05 (Bonferroni‑adjusted). The script writes `data/results/power_analysis.json` with fields `n_simulations`, `effect_size`, `estimated_power`, `power_ci_lower`, `power_ci_upper`, `method`.  
  - Requirements satisfied: FR‑005, SC‑004, reproducibility (fixed seed).  
  - Verification: script runs, JSON exists, `estimated_power` is a number in [0, 1], and two runs with identical seed produce identical JSON files.

- [ ] T010 [P] **Invalid‑workflow exclusion verification** – `code/utils/verify_invalid_exclusion.py` cross‑checks `data/raw/workflows.json` for `is_valid:false` entries and ensures they do **not** appear in `tradeoff_curve.csv`. It writes `data/results/invalid_exclusion_report.json` with `invalid_workflow_count`, `excluded_count`, and `status` (`"passed"` or `"failed"`).  
  - Requirements satisfied: FR‑008, edge‑case handling (US‑1).  
  - Verification: script exits 0, report file exists, and `excluded_count` equals the number of invalid workflows; the CSV contains no rows originating from those workflows.

- [ ] T011 [P] **Add trade‑off‑curve schema** – create `contracts/tradeoff_curve.schema.yaml` that mirrors the columns of `tradeoff_curve.csv` (numeric `reduction_pct`, `error_rate`, `std_dev`, `n_samples`).  
  - Requirements satisfied: Constitution IV (single source of truth).  
  - Verification: schema file exists and can be used by a validation script without errors.

- [ ] T012 [P] **Validate trade‑off‑curve CSV against schema** – `code/utils/validate_tradeoff_csv.py` runs `jsonschema` validation of `data/results/tradeoff_curve.csv` (converted to JSON records) against `contracts/tradeoff_curve.schema.yaml`. Failure aborts the pipeline.  
  - Requirements satisfied: Constitution IV, SC‑004.  
  - Verification: script returns exit 0 on valid CSV, non‑zero on schema mismatch.

## Phase 2 – Orchestration, reproducibility, and reporting

- [ ] T013 [P] **Orchestrator / main pipeline** – `code/main.py` provides a CLI that runs the full workflow in order: generator → Oracle (implicit) → full executor → compressed executor (for a list of depths, e.g., `0,2,4,6,8,10`) → step expander → analyzer → validation scripts → reporting. Flags include `--n-workflows`, `--seed`, `--depths`, and `--adaptive` (optional).  
  - Requirements satisfied: FR‑001 – FR‑007, overall pipeline cohesion.  
  - Verification: `python code/main.py --help` prints usage and exits 0; a smoke run `python code/main.py --n-workflows 20 --seed 42 --depths 0,2,4` completes in < 2 min and all expected output files from Phases 1‑2 exist.

- [ ] T014 [P] **Record total wall‑clock time** – `code/utils/measure_runtime.py` is invoked by the orchestrator to capture start and end timestamps, compute elapsed seconds, and write `data/results/run_metrics.json` (fields `total_wall_clock_time_seconds`, `start_timestamp`, `end_timestamp`).  
  - Requirements satisfied: SC‑005.  
  - Verification: after a pipeline run, `run_metrics.json` exists and the elapsed time is ≤ 21600 seconds (6 h).

- [ ] T015 [P] **Reproducibility report with checksums** – `code/utils/reproducibility_report.py` is invoked after successful completion and creates `data/results/reproducibility_report.json` containing:  
  * the exact command line used,  
  * SHA‑256 checksums for every file under `data/` (raw, processed, results),  
  * an aggregate `reproducibility_hash` (hash of concatenated checksums).  
  - Requirements satisfied: FR‑007, Constitution V, SC‑005.  
  - Verification: after two consecutive runs with identical parameters, a diff of the two JSON files shows no differences in the checksum fields.

- [ ] T016 [P] **Update project‑state YAML with artifact hashes** – `code/utils/update_state_yaml.py` reads `data/results/reproducibility_report.json`, extracts the checksums, and writes them into `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml` under `artifact_hashes`.  
  - Requirements satisfied: Constitution III & V (data hygiene & versioning).  
  - Verification: after pipeline run, the state YAML contains a key for each artifact and the values match the hashes in the reproducibility report.

- [ ] T017 [P] **Verify Oracle Policy Engine independence** – `code/tests/integration/test_oracle_independence.py` uses static analysis to assert that `code/models/policy.py` does not import any symbols from `code/services/compression.py` or `code/services/executor_compressed.py`.  
  - Requirements satisfied: Constitution VI, FR‑008.  
  - Verification: test passes; any import from compression modules causes a failure.

- [ ] T018 [P] **Abort pipeline on unsafe threshold** – `code/services/analyzer.py` raises a custom `UnsafeThresholdError` if the predicted error rate exceeds 1 % before writing final artifacts. The orchestrator catches this and exits with a clear message.  
  - Requirements satisfied: FR‑006 (safe‑zone enforcement).  
  - Verification: simulated run with exaggerated compression triggers abort; exit code non‑zero and message logged.

- [ ] T019 [P] **Validate numeric claims in results documentation** – `code/utils/validate_results_claims.py` parses `specs/001-policy-compression-tradeoff/results.md`, extracts reported numbers, and cross‑checks them against the corresponding values in `data/results/*.json` and `tradeoff_curve.csv`.  
  - Requirements satisfied: Constitution IV, SC‑001‑SC‑004.  
  - Verification: script exits 0 when all claims match; otherwise it reports mismatches and aborts.

- [ ] T020 [P] **Verify reproducibility hash matches state YAML** – `code/utils/check_reproducibility_hash.py` reads the hash from `data/results/reproducibility_report.json` and from `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`, asserts equality.  
  - Requirements satisfied: Constitution V.  
  - Verification: test passes; any mismatch causes pipeline failure.

- [ ] T021 [P] **Generate trade‑off figure** – `code/utils/make_figure.py` reads `tradeoff_curve.csv` and produces `figures/tradeoff_curve.png` (line plot with error bars and the identified safe‑zone threshold marked).  
  - Requirements satisfied: SC‑004, FR‑006, paper‑ready artifact.  
  - Verification: script runs without error, PNG file exists, and its dimensions are ≥ 600 px width.

- [ ] T022 [P] **Results documentation for paper handoff** – author `specs/001-policy-compression-tradeoff/results.md` that (a) describes the methods (deterministic generator, Oracle, BFS/DFS compression, GEE analysis, power analysis), (b) reports the key numbers (safe‑zone threshold with 95 % CI, estimated power, number of invalid workflows excluded), (c) references the exact artifact paths (`figures/tradeoff_curve.png`, `data/results/tradeoff_curve.csv`, `data/results/threshold_report.json`, `data/results/multiplicity_tests.json`, `data/results/power_analysis.json`, `data/results/reproducibility_report.json`), and (d) notes any edge‑case handling (`"[deferred]"` cases).  
  - Requirements satisfied: SC‑001‑SC‑004, Constitution IV, FR‑006.  
  - Verification: markdown file exists, each numeric claim matches the corresponding value in its source JSON/CSV (checked by `validate_results_claims.py`).

- [ ] T023 [P] **Paper‑stage handoff note** – create `specs/001-policy-compression-tradeoff/paper_handoff.md` that lists all artifacts required for the manuscript, includes the `reproducibility_hash`, and states that these satisfy Constitution IV (single source of truth) and V (hash verification).  
  - Requirements satisfied: FR‑006, Constitution IV & V.  
  - Verification: file exists, contains a bullet list with the exact relative paths, and the hash matches the value recorded in `reproducibility_report.json`.

## Dependency ordering (explicit)

1. T001 → 2. T002 → 3. T003 → 4. T004 → 5. T005 → 6. T006 → 7. T007 → 8. T008 → 9. T009 → 10. T010 → 11. T011 → 12. T012 → 13. T013 → 14. T014 → 15. T015 → 16. T016 → 17. T017 → 18. T018 → 19. T019 → 20. T020 → 21. T021 → 22. T022 → 23. T023

All tasks write only to project‑owned locations (`code/`, `data/`, `figures/`, `contracts/`, `specs/`, `state/`). No task touches platform‑owned `state/` directories beyond the permitted state YAML update. The entire pipeline is CPU‑only, respects the free‑tier CI resource limits, and each output can be deterministically validated.