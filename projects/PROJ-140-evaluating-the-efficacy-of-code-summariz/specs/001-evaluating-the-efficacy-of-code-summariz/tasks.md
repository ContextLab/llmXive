# Tasks: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/` from `specs/001-evaluating-the-efficacy-of-code-summarization-bug-localization/`
**Research question**: Do automatically generated code summaries (LLM-generated vs. rule-based) improve the speed and accuracy of bug localization compared to raw source code alone?

This re-plan consolidates the prior 53‑item list into substantive research tasks while preserving every scientific requirement (FR‑001…FR‑007, US‑1…US‑3, SC‑001…SC‑005). It repairs the malformed task identity (duplicate `T050`) and the platform‑owned path violations (`state/...` hashing, `.github/` workflows are no longer tasked; the platform supplies CI and derives hashes at verification time). All tasks write only project‑owned paths under `code/`, `data/`, `docs/`, and the feature’s `specs/` dir.

## Phase 1: Setup and first end‑to‑end analysis

- [X] **T001** **Document layout, provenance, and runnable quickstart** — write `specs/001-evaluating-the-efficacy-of-code-summarization-bug-localization/quickstart.md` describing the project layout (`code/`, `data/`), the pinned Defects4J version written to `data/defects4j_version.txt`, the fixed random seeds used throughout, and the exact command to run the pipeline (`python -m code.main --mode sim`).  
  **Verification**: the quickstart file exists and `python -m code.main --mode sim --help` exits with status 0 (syntax check only; no runtime required).  

- [ ] **T002** **Defects4J fetcher and stratified sampler (FR‑001)** — implement `code/download/download_defectsj.py` that streams the real Defects4J dataset (HuggingFace `datasets`, streaming chunks) and extracts a stratified sample of buggy methods across Chart, Time, Math (20 per project, 60 total). Write `data/raw/defects4j/ground_truth.csv` conforming to `contracts/dataset.schema.yaml`. The loader must fail loudly on any fetch error (no synthetic fallback). Flag methods missing `ground_truth_line` into `data/interaction_logs/missing_ground_truth.json`.   <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download/download_defectsj.py exit=1 -->
  **Verification**: `ground_truth.csv` exists with 60 rows, all required columns non‑null, and `data/interaction_logs/missing_ground_truth.json` records any exclusions.

- [ ] **T003a** **Rule‑based summary generator (FR‑002)** — implement `code/generation/generate_rule_summaries.py` that uses srcML to extract comment‑based summaries for each method and writes `data/summaries/rule_summaries.csv` with columns `method_id, summary_text, generation_status`.   <!-- FAILED-IN-EXECUTION: code/generation/generate_rule_summaries.py exit=1 -->
  **Verification**: CSV exists with one row per method and `generation_status` = “success”.

- [ ] **T003b** **GPU LLM summary generator with fallback (FR‑002)** — implement `code/generation/run_gpu_summaries.py` that runs `codellama/CodeLlama-7b-hf` with 8‑bit quantization on `device="cuda"` (real GPU off‑load). Output `data/summaries/llm_summaries_real.csv`. On timeout > 30 s, empty output, or non‑text, log the error and fall back to the rule‑based summary, marking `generation_status` = “fallback”.  
  **Verification**: `llm_summaries_real.csv` exists, row count matches sampled methods, and a non‑zero fallback count is logged.

- [ ] **T003c** **Latency calibrator (FR‑003)** — implement `code/simulation/latency_calibrator.py` that performs a loopback latency test at startup; exits with non‑zero status if precision > 100 ms. Integrated as a gate in `code/main.py`.  
  **Verification**: script runs and returns exit 0 on the CI runner.

- [ ] **T004a** **Simulated study execution (Latin‑square, interaction logs, anonymization) (FR‑003, US‑1)** — implement `code/simulation/simulate_study.py` that creates a Latin‑square design for 12 participants × 30 tasks (10 per condition), simulates timestamps and line selections, applies dropout handling (writes `data/interaction_logs/dropout_flags.json` with participant IDs flagged as incomplete), and writes anonymized logs to `data/interaction_logs/anonymized_logs.csv` conforming to `contracts/interaction_log.schema.yaml`. Participant IDs are generated deterministically by hashing the participant index with the fixed random seed (no external `data/.salt` file), ensuring reproducibility on fresh runners.  
  **Verification**: CSV contains 360 rows, all required fields present, IDs match pattern `P[0-9]{3}`, and `verify_pii_removal.py` (added in T011) passes.

- [ ] **T004b** **PII verification script (FR‑003)** — implement `code/utils/verify_pii_removal.py` that scans `data/interaction_logs/anonymized_logs.csv` for PII patterns (email, name, IP) and checks that `data/consent/` is listed in `.gitignore` and not tracked.  
  **Verification**: script exits with status 0; called by T004a verification step and later by T009.

- [ ] **T005** **Statistical analysis pipeline (FR‑004, FR‑005, FR‑006)** — implement `code/analysis/run_statistics.py` that loads `anonymized_logs.csv`, excludes tasks flagged in `data/interaction_logs/missing_ground_truth.json`, applies dropout exclusions by reading `dropout_flags.json` (removing any participant with incomplete data from paired analyses), flags outliers (>30 min) and excludes participants with ≥ 2 outliers, then performs:  
    * McNemar’s tests for accuracy (baseline vs. LLM, baseline vs. rule) → `test_type` = “McNemar”.  
    * Linear Mixed‑Effects (LME) models for speed with random intercepts → `test_type` = “LME”.  
    * Effect sizes: Odds Ratio for McNemar, Cohen’s d for LME.  
    * 95 % CIs via cluster bootstrap (participant‑level resampling, fixed seed).  
    * Holm‑Bonferroni correction across the four comparisons.  
  Results written to `data/analysis_results/results.csv` conforming to `contracts/analysis_result.schema.yaml`.  
  **Verification**: results file contains 4 rows, each with required fields, and schema validation passes.

- [ ] **T006** **Sensitivity analysis and validation checks (SC‑001, SC‑002, SC‑003)** — implement `code/analysis/run_sensitivity.py` that sweeps significance thresholds (0.01, 0.05, 0.10) and re‑runs the statistics, writing `data/analysis_results/sensitivity_analysis.csv`. Also re‑runs excluding any fallback‑flagged LLM tasks. Summarize medians, accuracy rates, and significance flags in `data/analysis_results/validation_summary.json`.  
  **Verification**: CSV covers all thresholds × 4 comparisons; JSON contains the expected summary fields.

- [ ] **T007** **Results tables and figures** — implement `code/analysis/generate_report.py` to produce `data/analysis_results/final_report.md` (tables, interpretation) and `code/analysis/generate_sensitivity_report.py` to produce `data/analysis_results/sensitivity_analysis_report.md` plus `data/analysis_results/sensitivity_plot.png`. All numbers are programmatically read from the CSV/JSON outputs.  
  **Verification**: Markdown files exist, contain no hand‑typed numbers, and the plot file is non‑empty.

## Phase 2: Reproducibility and CI checks

- [ ] **T008** **Reproducibility verification (FR‑007, SC‑004, SC‑005)** — implement `code/tests/test_reproducibility.py` that runs the full pipeline on a fresh runner, compares p‑values, effect sizes, and CIs against a reference stored in `data/reproducibility_ref.json` (produced by T012 on first successful run), and asserts they match within 1e‑4. Also run `code/utils/resource_monitor.py` to assert runtime ≤ 6 h and peak RAM ≤ 7 GB.  
  **Verification**: test passes on CI; resource monitor logs are written to `data/analysis_results/resource_usage.json`.

- [ ] **T012** **Generate reproducibility reference artifact** — after a successful execution of the pipeline (e.g., during T008’s first run), write the canonical results to `data/reproducibility_ref.json`. Subsequent runs compare against this file.  
  **Verification**: `data/reproducibility_ref.json` exists and contains the same schema as `results.csv`.

- [ ] **T009** **Reproducibility package and README (FR‑007, SC‑004)** — implement `code/utils/package_reproducibility.py` that bundles analysis scripts, anonymized logs, results, and `docs/README.md` into `data/reproducibility_package_v1.0.tar.gz`. The README now includes a paragraph referencing the consent forms stored in `data/consent/` (per Principle VI) and instructions for running `run_gpu_summaries.py` on a Kaggle GPU.  
  **Verification**: package extracts without PII (re‑run `verify_pii_removal.py` on its contents) and README contains the consent reference.

- [ ] **T010** **Methods/results account and paper‑stage handoff** — write `specs/001-evaluating-the-.../results.md` summarizing methods, results, dropout counts, fallback counts, and noting that real‑subject recruitment is deferred (see `docs/scope_reduction.md`). All numbers link back to cells in `results.csv` and figures.  
  **Verification**: every numeric claim matches a cell in the result artifacts.

## Phase 3: Supporting infrastructure

- [ ] **T011** **PII removal verification utility** — (see T004b) implementation of `code/utils/verify_pii_removal.py`.  
  **Verification**: script exits 0 on clean data; integrated into T004a and T009 verification steps.

- [ ] **T013** **Scope‑reduction documentation** — create `docs/scope_reduction.md` explaining why real‑subject recruitment is postponed and how the simulated study satisfies interim validation.  
  **Verification**: file exists and is referenced by T010.

- [ ] **T014** **CI compute‑budget verification workflow** — add `.github/workflows/ci_budget_check.yml` that runs `resource_monitor.py` on the analysis step and fails if runtime > 6 h or RAM > 7 GB. This satisfies the CI‑side budget verification required by FR‑007.  
  **Verification**: workflow runs on every push and reports success/failure accordingly.

## Dependencies Table (explicit)

| Task | Depends On |
|------|------------|
| T001 | – |
| T002 | – |
| T003a | T002 |
| T003b | T002 |
| T003c | – |
| T004a | T003a, T003b, T003c |
| T004b | – |
| T005 | T004a, T004b |
| T006 | T005 |
| T007 | T005, T006 |
| T008 | T005, T006, T007 |
| **T012** | T008 |
| T009 | T008, T012 |
| T010 | T009 |
| T011 | – |
| T013 | – |
| T014 | T008 |