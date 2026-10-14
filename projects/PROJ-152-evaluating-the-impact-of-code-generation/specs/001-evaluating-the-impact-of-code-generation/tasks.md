---
description: "Task list for Evaluating the Impact of Code Generation Models on Code Security"
---

# Tasks: Evaluating the Impact of Code Generation Models on Code Security

**Input**: Design documents from `/specs/001-code-security-evaluation/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: Optional – include only if explicitly required in the specification.

**Organization**: Tasks are grouped by phase.  
`- [ ] T### [P] [USx] description (file path)`  

* `[P]` = may run in parallel (different files, no dependencies)  
* `[USx]` = user‑story identifier (e.g., US1, US2, US3) – omitted for foundational tasks.

## Phase 0 – Spec & Plan Alignment (CRITICAL GATE)

- [X] T000b [P] **ALIGN PLAN** – Update the summary section of `plan.md` so it matches the amended `spec.md`. *(plan.md)*
- [X] T000c [P] **UPDATE COVERAGE MAP** – Revise the FR/SC coverage map in `plan.md` to remove undefined FR‑006‑FR‑009 and SC‑001‑SC‑004 entries, and ensure all referenced IDs exist in `spec.md`. *(plan.md)*
- [ ] T000d [P] **VERIFY PLAN ALIGNMENT** – Confirm that the plan’s coverage map aligns with `spec.md`; edit `plan.md` to eliminate any undefined FR or SC identifiers and obtain reviewer sign‑off. *(plan.md)*
- [~] T042 [P] **CONSTITUTION PROMPT SET AMENDMENT** – Propose and document an amendment to Constitution Principle VII to reflect the approved pilot prompt set of 30 prompts (10 CodeXGLUE + 20 handcrafted) and obtain reviewer approval. *(constitution.md)*

## Phase 1 – Project Setup & Core Infrastructure

- [X] T001a [P] Create project root `projects/PROJ-152-evaluating-the-impact-of-code-generation/` with sub‑directories `code/`, `data/`, `tests/`, `docs/`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/)*
- [X] T001b [P] Add `requirements.txt` (pinned versions of `transformers`, `torch‑cpu`, `bitsandbytes‑cpu`, `scikit‑learn`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `bandit`, `semgrep`, `codeql`). *(projects/PROJ-152-evaluating-the-impact-of-code-generation/requirements.txt)*
- [ ] T001c [P] Initialise a Python 3.11 virtual environment (`python -m venv venv`) and install `requirements.txt`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/)*
- [ ] T002 [P] Configure linting (ruff) and formatting (black) via `pyproject.toml`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/pyproject.toml)*
- [ ] T003 [P] Create `code/config.py` with global seeds, path constants (`DATA_ROOT`, `PROMPT_MANIFEST`, …), and model hyper‑parameters (`max_tokens=256`, `batch_size=1`). *(code/config.py)*
- [ ] T004 [P] Implement `code/update_state.py` to manage `state.yaml` and compute SHA‑256 hashes for all artefacts (Constitution Principle V). *(code/update_state.py)*
- [ ] T005 [P] Implement `code/download.py` that:
  1. Downloads the CodeXGLUE *code‑to‑text* dataset via `datasets.load_dataset`,
  2. Filters prompts containing any of the security keywords list `["SQL","XSS","auth","injection","sanitize","password","token"]`,
  3. Ranks filtered prompts by the total number of keyword occurrences and selects the **top 10** most relevant prompts,
  4. Writes `data/prompts/filtered_codexglue.json` and records its checksum. *(code/download.py)*
- [ ] T006 [P] Create `data/prompts/handcrafted.json` containing **20 handcrafted web‑security prompts** (5 each for Database Access, HTML Rendering, Authentication, Injection) and generate its checksum. *(data/prompts/handcrafted.json)*
- [ ] T007 [P] Add `data/mappings/nist_severity_map.yaml` mapping textual severity levels to an ordinal scale (e.g., `HIGH: 4`, `MEDIUM: 3`, `LOW: 2`, `INFO: 1`). *(data/mappings/nist_severity_map.yaml)*
- [ ] T008a [P] Implement `code/generate.py` that:
  - Loads StarCoder‑Base, CodeGen‑2B, and GPT‑NeoX‑1.3B with **4‑bit CPU quantization** via `bitsandbytes`,
  - Enforces a per‑snippet generation timeout of 120 s using `signal.alarm`,
  - Logs timeouts or generation failures to `data/failures.log`. *(code/generate.py)*
- [ ] T008b [P] Implement `code/orchestrator.py` that:
  - Tracks cumulative wall‑clock time,
  - Stops the pipeline early if `elapsed + estimated_remaining > 6 h` and writes a “Time Budget Exceeded” warning to `data/failures.log`,
  - Emits `data/runtime_log.json` with start/end timestamps and status flags. *(code/orchestrator.py)*
- [ ] T009 [P] Implement `code/analyze.py` that:
  - Invokes Bandit (Python), Semgrep (security‑best‑practices ruleset), and CodeQL (Java/JS) on each generated snippet,
  - Enforces a configurable per‑scanner timeout (e.g., 60 s) via `subprocess.run(..., timeout=…)`,
  - Writes raw scanner outputs to `data/findings/raw/<model>_<scanner>.jsonl`. *(code/analyze.py)*
- [ ] T010 [P] Implement `code/prompts.py` that merges `filtered_codexglue.json` (T005) and `handcrafted.json` (T006) into a single `data/prompts/manifest.json`, adds source attribution, and records a checksum. *(code/prompts.py)*
- [ ] T011 [P] [US1] Integration test for the generation pipeline with timeout handling (`tests/integration/test_generate.py`). *(tests/integration/test_generate.py)*
- [ ] T012 [P] [US1] Contract test asserting the CSV schema of scanner outputs (`tests/contract/test_scanner_output.py`). *(tests/contract/test_scanner_output.py)*
- [ ] T013 [P] Extend `code/generate.py` with a **model‑loader** that:
  - Instantiates each model once,
  - Keeps them in memory (≈ 4 GB total) using 4‑bit quantization,
  - Monitors system RAM via `psutil.virtual_memory()` and, if used RAM exceeds **80 %**, unloads the currently idle model before loading the next to keep peak usage below the threshold. *(code/generate.py)*
- [ ] T018 [P] **ARCHIVE ARTIFACTS** – After pipeline completion, compress all `data/` sub‑directories into `artifacts/run_<run_id>.tar.gz` and record its checksum. *(code/archive.py)*
- [ ] T019 [P] **GENERATE FINAL REPORT** – Assemble a markdown `reports/final_report.md` summarizing methods, results, and compliance with all FR/SC, referencing the generated CSVs and figures. *(reports/final_report.md)*

## Phase 2 – Core Data Production (User Story 1)

- [ ] T014 [US1] **Generation Loop** – In `code/generate.py`, iterate over `data/prompts/manifest.json` (30 prompts) and generate code for each model (total 90 snippets). Write a CSV `data/generated/snippets.csv` with columns  
  `snippet_id, model_name, prompt_id, code, loc, generation_time, status, error_message`.  
  Produce a SHA‑256 checksum file `snippets.csv.sha256` and log any generation failures to `data/failures.log`. *(data/generated/snippets.csv)*
- [ ] T015 [US1] **Scanner Runner** – In `code/analyze.py`, read `snippets.csv` and pipe each snippet through Bandit, Semgrep, and CodeQL, respecting the per‑scanner timeout. Store a unified CSV `data/findings/raw_findings.csv` with columns  
  `finding_id, snippet_id, model_name, scanner, cwe_id, raw_severity, finding_text`. *(data/findings/raw_findings.csv)*
- [ ] T016a [US1] **Severity Mapping** – Implement `code/metrics.py` to translate scanner‑specific severity labels to the NIST ordinal scale defined in `nist_severity_map.yaml`. *(code/metrics.py)*
- [ ] T016b [US1] **CWE Extraction** – Extend `code/metrics.py` to reliably parse CWE identifiers from each scanner’s output (Bandit, Semgrep, CodeQL) and add a `cwe_id` column to `raw_findings.csv`. *(code/metrics.py & data/findings/raw_findings.csv)*
- [ ] T017 [US1] **Failure Logging** – Ensure `code/analyze.py` logs empty snippets, unsupported languages, and scanner crashes to `data/failures.log` with clear error codes. *(code/analyze.py)*

## Phase 3 – Calibration & Metric Computation (User Story 2)

- [ ] T022a [US2] **Calibration Template** – In `code/calibration.py`, generate `data/calibration/calibration_template.csv` containing `snippet_id, model_name, prompt_id, human_label (empty)`. Also create `data/calibration/instructions.md` that guides human experts on labeling true vulnerabilities. *(code/calibration.py, data/calibration/calibration_template.csv, data/calibration/instructions.md)*
- [ ] T022b [US2] **Manual Annotation** – Human experts label the **30 calibration snippets** (10 per model) using the template from T022a. Output stored as `data/calibration/human_labels.csv`. *(data/calibration/human_labels.csv)*
- [ ] T022c [US2] **FPR Computation** – Extend `code/calibration.py` to read `raw_findings.csv` and `human_labels.csv`, compute per‑scanner & per‑model Inter‑Rater Reliability (Cohen’s κ) and **False Positive Rate (FPR)**. Write `data/calibration/fpr_stats.csv`. *(code/calibration.py, data/calibration/fpr_stats.csv)*
- [ ] T022d [US2] **Label Validation** – Add a validation step in `code/calibration.py` that checks `human_labels.csv` for required columns, non‑empty rows, and consistent `snippet_id`s. Emit `data/calibration/validation_report.json`; abort the pipeline if validation fails. *(code/calibration.py, data/calibration/validation_report.json)*
- [ ] T023 [US2] **Raw Metrics** – In `code/metrics.py`, join `raw_findings.csv` with `snippets.csv` to compute:
  - Vulnerabilities per 100 LOC (V/100 LOC),
  - Mean severity (using the ordinal scale from T016a).  
  Output `data/results/raw_metrics.csv`. *(data/results/raw_metrics.csv)*
- [ ] T023b [US2] **FPR‑Corrected Metrics** – Using `fpr_stats.csv` (T022c), adjust vulnerability counts to compensate for scanner false positives. Write `data/results/corrected_metrics.csv`. *(data/results/corrected_metrics.csv)*
- [ ] T020 [P] [US2] Unit test for V/100 LOC calculation (`tests/unit/test_metrics.py`). *(tests/unit/test_metrics.py)*
- [ ] T021 [P] [US2] Unit test for Bonferroni‑adjusted p‑values (`tests/unit/test_stats.py`). *(tests/unit/test_stats.py)*
- [ ] T024 [US2] **Kruskal‑Wallis Test** – Implement `code/stats.py` to run a Kruskal‑Wallis test on **raw** V/100 LOC across the three models (input `raw_metrics.csv`). Store results in `data/results/kw_results.csv`. *(data/results/kw_results.csv)*
- [ ] T025 [US2] **Dunn Post‑hoc** – If the KW p‑value < 0.05, run Dunn’s test with Bonferroni correction (α = 0.0167). Write `data/results/dunn_results.csv`. *(data/results/dunn_results.csv)*
- [ ] T026 [US2] **Zero‑Inflated Negative Binomial (ZINB)** – Conditional execution: if the proportion of zero V/100 LOC observations > 50 % (computed from `raw_metrics.csv`), fit a ZINB model (`statsmodels.discrete.ZeroInflatedNegativeBinomialP`) with formula  
  `vuln_count ~ C(model_name) + offset(log(loc))`. Output `data/results/zinb_results.csv`. *(data/results/zinb_results.csv)*
- [ ] T027 [US2] **Sensitivity Sweep** – In `code/sensitivity.py`, vary the high‑severity cutoff (e.g., severity ≥ 4, ≥ 5) and recompute the proportion of “high‑risk” snippets using `corrected_metrics.csv`. Store results in `data/results/sensitivity_analysis.csv`. *(data/results/sensitivity_analysis.csv)*
- [ ] T028 [US2] **Statistical Summary** – Consolidate all test outputs (`kw_results.csv`, `dunn_results.csv`, optional `zinb_results.csv`) into a single `data/results/statistical_summary.csv` containing: test name, statistic, raw p‑value, adjusted p‑value, and a pass/fail conclusion. *(data/results/statistical_summary.csv)*
- [ ] T029 [US2] **Final Sensitivity Table** – Produce `data/results/sensitivity_table.csv` summarising each severity cutoff, the corresponding high‑risk proportion per model, and confidence intervals. *(data/results/sensitivity_table.csv)*
- [ ] T034 [US3] **Run Summary Generation** – Create `data/results/run_summary.csv` containing:
  - Total snippets (90),
  - Completion rate (≥ 90 % as required by SC‑005),
  - Number of generation failures,
  - Number of analysis failures,
  - Wall‑clock time (from `runtime_log.json`). *(data/results/run_summary.csv)*
- [ ] T034a [US3] **Completion‑Rate Assertion** – Add a verification step that reads `run_summary.csv` and asserts `completion_rate_generation >= 0.90` and `completion_rate_analysis >= 0.90`; fail the pipeline if the condition is not met. *(code/verify_completion.py)*

## Phase 4 – Visualisations & Reporting (User Story 3)

- [ ] T031 [US3] In `code/viz.py`, generate a **box‑plot** (`figures/boxplot_vuln_density.png`) of V/100 LOC per model (median, quartiles, outliers). *(code/viz.py)*
- [ ] T032 [US3] In `code/viz.py`, generate a **CWE heat‑map** (`figures/cwe_heatmap.png`) showing frequency of each CWE across prompt categories and models. *(code/viz.py)*
- [ ] T030 [P] [US3] Integration test that runs the full visualization pipeline and checks that three output files are produced (`figures/boxplot_vuln_density.png`, `figures/cwe_heatmap.png`, `data/results/run_summary.csv`). *(tests/integration/test_viz.py)*
- [ ] T035 [US3] Update `state.yaml` (via `code/update_state.py`) with SHA‑256 hashes for all new artefacts and a fresh `updated_at` timestamp. *(state.yaml)*

## Phase 5 – Polish & Cross‑Cutting Concerns

- [ ] T036a [P] Refresh `README.md` with an overview, installation steps, and a clear statement of the **N = 30 prompt** scope. *(README.md)*
- [ ] T036b [P] Populate `docs/quickstart.md` with a step‑by‑step guide to run the entire pipeline on the GitHub‑Actions runner. *(docs/quickstart.md)*
- [ ] T036c [P] Update `docs/research.md` with the finalized methodology, limitations, and justification of the FPR‑correction approach. *(docs/research.md)*
- [ ] T037a [P] Code cleanup – remove any unused imports across all modules in `code/`. *(code/*)*
- [ ] T037b [P] Run `black` (and `ruff` lint) across the repository to enforce formatting standards. *(.)*
- [ ] T037c [P] Add docstrings to every public function and class in `code/`. *(code/*)*
- [ ] T038 [P] **Optimise model loading/unloading** – Implement a deterministic loading order (StarCoder → generate → unload, then CodeGen → generate → unload, then NeoX → generate → unload) and verify that peak RAM usage is reduced by at least **10 %** compared to a naïve sequential load; record peak usage in `runtime_log.json`. *(code/generate.py)*
- [ ] T039 [P] Add edge‑case unit tests in `tests/unit/` (e.g., empty prompt, unsupported language). *(tests/unit/*)*
- [ ] T040 [P] Harden handling of generated code: ensure snippets are never executed, only written to disk and analysed statically. *(code/generate.py, code/analyze.py)*
- [ ] T041 [P] Execute `quickstart.md` validation script to confirm the documentation matches the actual pipeline behaviour. *(docs/quickstart.md)*