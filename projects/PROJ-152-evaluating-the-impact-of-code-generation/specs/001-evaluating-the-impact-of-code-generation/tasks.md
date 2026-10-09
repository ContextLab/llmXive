---
description: "Task list for Evaluating the Impact of Code Generation Models on Code Security"
---

# Tasks: Evaluating the Impact of Code Generation Models on Code Security

**Input**: Design documents from `/specs/001-code-security-evaluation/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – include them only if explicitly requested in the specification.

**Organization**: Tasks are grouped by phase and, where appropriate, by user story to enable independent implementation and testing.

## Format
`- [ ] T### [P?] [Story] Description (file path)`

- **[P]** – can run in parallel (different files, no dependencies)  
- **[Story]** – which user story this task belongs to (e.g., US1, US2, US3)  

---

## Phase 0 – Spec & Plan Alignment (CRITICAL GATE)

**Purpose**: Resolve requirement conflicts and formally amend scope before any implementation begins.

- [X] T000a [P] **AMEND SPEC** – Update `spec.md` (FR‑002, SC‑005) to explicitly reflect the amended scope of **N = 30 prompts** (10 CodeXGLUE + 20 handcrafted) and **N = 90 snippets**. Document the GitHub‑Actions RAM & time limits as justification. *(spec.md)*
- [X] T000b [P] **ALIGN PLAN** – Update the summary section of `plan.md` so it matches the amended `spec.md`. *(plan.md)*
- [X] T000c [P] **UPDATE COVERAGE MAP** – Revise the FR/SC coverage map in `plan.md` to reference the amended FR‑002 (N = 30) and SC‑005 (6 h CPU‑only limit). *(plan.md)*

---

## Phase 1 – Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic tooling.

- [X] T001a [P] Create project root `projects/PROJ-152-evaluating-the-impact-of-code-generation/` with sub‑directories `code/`, `data/`, `tests/`, `docs/`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/)*
- [X] T001b [P] Add `requirements.txt` (pinned versions of `transformers`, `torch‑cpu`, `bitsandbytes‑cpu`, `scikit‑learn`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `bandit`, `semgrep`, `codeql`). *(projects/PROJ-152-evaluating-the-impact-of-code-generation/requirements.txt)*
- [X] T001c [P] Initialise a Python 3.11 virtual environment (`python -m venv venv`) and install `requirements.txt`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/)*
- [X] T002 [P] Configure linting (ruff) and formatting (black) tools via `pyproject.toml`. *(projects/PROJ-152-evaluating-the-impact-of-code-generation/pyproject.toml)*

---

## Phase 2 – Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be in place before any user story can start.

- [X] T003 [P] Create `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/config.py` with:
  - Global random seeds,
  - Path constants (`DATA_ROOT`, `PROMPT_MANIFEST`, etc.),
  - Model hyper‑parameters (`max_tokens=256`, `batch_size=1`).
- [X] T004 [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/update_state.py` to manage `state.yaml` and compute SHA‑256 hashes for all artefacts (Constitution Principle V).  
- [X] T005 [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/download.py` that:
  1. Downloads the CodeXGLUE *code‑to‑text* dataset via `datasets.load_dataset`,
  2. Filters prompts containing security keywords (`SQL`, `XSS`, `auth`, `injection`, `sanitize`, `password`, `token`),
  3. Selects the **10 most relevant** prompts (manual review step documented),
  4. Writes `data/prompts/filtered_codexglue.json` and records its SHA‑256 checksum.  
- [X] T006 [P] Create `projects/PROJ-152-evaluating-the-impact-of-code-generation/data/prompts/handcrafted.json` containing **20 handcrafted web‑security prompts** (5 each for Database Access, HTML Rendering, Authentication, Injection) and generate its checksum.  
- [X] T007 [P] Add `projects/PROJ-152-evaluating-the-impact-of-code-generation/data/mappings/nist_severity_map.yaml` mapping textual severity levels to an ordinal scale (e.g., `HIGH: 4`, `MEDIUM: 3`, `LOW: 2`, `INFO: 1`).  
- [X] T008a [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/generate.py`:
  - Loads the three models (StarCoder‑Base, CodeGen‑2B, GPT‑NeoX‑1.3B) with **4‑bit CPU quantization** via `bitsandbytes`,
  - Provides a **per‑snippet timeout** (default 120 s) using `signal.alarm`,
  - Logs any timeouts or generation failures to `data/failures.log`.  
- [X] T008b [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/orchestrator.py` that:
  - Tracks cumulative wall‑clock time,
  - Stops the pipeline early if `elapsed + estimated_remaining > 6 h` and writes a “Time Budget Exceeded” warning to `data/failures.log`,
  - Emits `data/runtime_log.json` with start/end timestamps and status flags.  
- [X] T009 [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/analyze.py` that:
  - Invokes Bandit (Python), Semgrep (security‑best‑practices ruleset), and CodeQL (Java/JS) on each generated snippet,
  - Enforces a **configurable per‑scanner timeout** (e.g., 60 s) via `subprocess.run(..., timeout=…)`,
  - Writes raw scanner outputs to `data/findings/raw/<model>_<scanner>.jsonl`.  
- [X] T010 [P] Implement `projects/PROJ-152-evaluating-the-impact-of-code-generation/code/prompts.py` that merges `filtered_codexglue.json` (T005) and `handcrafted.json` (T006) into a single `data/prompts/manifest.json`, adds source attribution, and records a checksum.  

**Checkpoint** – All foundational artefacts are in place; user‑story work may now proceed.

---

## Phase 3 – User Story 1 – Generate & Analyse Code Snippets (Priority P1) 🎯 MVP

**Goal**: Produce 90 code snippets (30 prompts × 3 models) and collect static‑analysis findings.

### Tests (optional)

- [X] T011 [P] [US1] Integration test for the generation pipeline with timeout handling (`tests/integration/test_generate.py`).  
- [X] T012 [P] [US1] Contract test asserting the CSV schema of scanner outputs (`tests/contract/test_scanner_output.py`).  

### Implementation

- [X] T013 [P] [US1] Extend `code/generate.py` with a **model‑loader** that:
  - Instantiates each model once,
  - Keeps them in memory (≈ 4 GB total) using 4‑bit quantization,
  - Releases a model before loading the next if memory pressure is detected.  
- [ ] T014 [US1] **Generation Loop** – In `code/generate.py`, iterate over `data/prompts/manifest.json` (30 prompts) and generate code for each model (total 90 snippets). Write a CSV `data/generated/snippets.csv` with columns:
  `snippet_id, model, prompt_id, code, line_count, generation_timestamp`.  
  Produce a SHA‑256 checksum file `snippets.csv.sha256` and log any generation failures to `data/failures.log`.  
- [X] T015 [US1] **Scanner Runner** – In `code/analyze.py`, read `snippets.csv` and pipe each snippet through Bandit, Semgrep, and CodeQL, respecting the per‑scanner timeout. Store unified CSV `data/findings/raw_findings.csv` with columns:
  `snippet_id, model, scanner, finding_id, cwe_id, severity_label, severity_score, file_path, line`.  
- [X] T016a [US1] **Severity Mapping** – Implement `code/metrics.py` to translate scanner‑specific severity labels to the NIST ordinal scale defined in `nist_severity_map.yaml`.  
- [ ] T016b [US1] **CWE Extraction** – Extend `code/metrics.py` to reliably parse CWE identifiers from each scanner’s output (Bandit, Semgrep, CodeQL) and add a `cwe_id` column to `raw_findings.csv`.  
- [X] T017 [US1] **Failure Logging** – Ensure `code/analyze.py` logs empty snippets, unsupported languages, and scanner crashes to `data/failures.log` with clear error codes.  

**Checkpoint** – Generation and raw analysis artefacts (`snippets.csv`, `raw_findings.csv`) are ready for downstream metrics.

---

## Phase 4 – User Story 2 – Metrics, Calibration & Statistical Inference (Priority P2)

**Goal**: Derive vulnerability density, apply FPR correction, and test for model differences.

### Tests (optional)

- [X] T020 [P] [US2] Unit test for V/100LOC calculation (`tests/unit/test_metrics.py`).  
- [X] T021 [P] [US2] Unit test for Bonferroni‑adjusted p‑values (`tests/unit/test_stats.py`).  

### Implementation

- [ ] T022a [US2] **Calibration Template** – In `code/calibration.py`, generate `data/calibration/calibration_template.csv` containing `snippet_id, model, prompt_id, human_label (empty)`. Also produce `data/calibration/instructions.md` that guides human experts on labeling true vulnerabilities.  
- [ ] T022b **MANUAL** – Human experts label the **30 calibration snippets** (10 per model) using the template from T022a. Output stored as `data/calibration/human_labels.csv`. *(placeholder for manual work)*  
- [ ] T022c [US2] **FPR Computation** – Extend `code/calibration.py` to read `raw_findings.csv` and `human_labels.csv`, compute per‑scanner & per‑model Inter‑Rater Reliability (Cohen’s κ) and **False Positive Rate (FPR)**. Write `data/calibration/fpr_stats.csv`.  
- [ ] T022d [US2] **Label Validation** – Add a validation step in `code/calibration.py` that checks `human_labels.csv` for required columns, non‑empty rows, and consistent `snippet_id`s. Emit `data/calibration/validation_report.json`; abort the pipeline if validation fails.  
- [ ] T023 [US2] **Raw Metrics** – In `code/metrics.py`, join `raw_findings.csv` with `snippets.csv` to compute:
  - Vulnerabilities per 100 LOC (V/100LOC),
  - Mean severity (using the ordinal scale from T016a).
  Output `data/results/raw_metrics.csv`.  
- [ ] T023b [US2] **FPR‑Corrected Metrics** – Using `fpr_stats.csv` (T022c), adjust vulnerability counts to compensate for scanner false positives. Write `data/results/corrected_metrics.csv`. *Note: corrected metrics are used only for sensitivity analysis, not for primary hypothesis testing (per Spec limitation).*  
- [X] T024 [US2] **Kruskal‑Wallis Test** – Implement `code/stats.py` to run a Kruskal‑Wallis test on **raw** V/100LOC across the three models (input `raw_metrics.csv`). Store results in `data/results/kw_results.csv`.  
- [X] T025 [US2] **Dunn Post‑hoc** – If the KW p‑value < 0.05, run Dunn’s test with Bonferroni correction (α = 0.0167). Write `data/results/dunn_results.csv`.  
- [ ] T026 [US2] **Zero‑Inflated Negative Binomial (ZINB)** – Conditional execution: if the proportion of zero V/100LOC observations > 50 % (computed from `raw_metrics.csv`), fit a ZINB model (`statsmodels.discrete.ZeroInflatedNegativeBinomialP`) with formula  
  `vuln_count ~ C(model) + offset(log(loc))`.  
  Output `data/results/zinb_results.csv`.  
- [ ] T027 [US2] **Sensitivity Sweep** – In `code/sensitivity.py`, vary the high‑severity cutoff (e.g., severity ≥ 4, ≥ 5) and recompute the proportion of “high‑risk” snippets using `corrected_metrics.csv`. Store results in `data/results/sensitivity_analysis.csv`.  
- [ ] T028 [US2] **Statistical Summary** – Consolidate all test outputs (`kw_results.csv`, `dunn_results.csv`, optional `zinb_results.csv`) into a single `data/results/statistical_summary.csv` containing: test name, statistic, raw p‑value, adjusted p‑value, and a pass/fail conclusion.  
- [ ] T029 [US2] **Final Sensitivity Table** – Produce `data/results/sensitivity_table.csv` summarising each severity cutoff, the corresponding high‑risk proportion per model, and confidence intervals.  

**Checkpoint** – All metric, calibration, and statistical artefacts are ready for reporting.

---

## Phase 5 – User Story 3 – Visualisations & Reporting (Priority P3)

**Goal**: Create publication‑ready figures and a concise run‑summary.

### Tests (optional)

- [ ] T030 [P] [US3] Integration test that runs the full visualization pipeline and checks that three output files are produced (`boxplot.png`, `cwe_heatmap.png`, `run_summary.csv`).  

### Implementation

- [ ] T031 [US3] In `code/viz.py`, generate a **box‑plot** (`figures/boxplot_vuln_density.png`) of V/100LOC per model (median, quartiles, outliers).  
- [ ] T032 [US3] In `code/viz.py`, generate a **CWE heat‑map** (`figures/cwe_heatmap.png`) showing frequency of each CWE across prompt categories and models.  
- [ ] T034 [US3] Create `data/results/run_summary.csv` containing:
  - Total snippets (90),
  - Completion rate (≥ 90 % as required by SC‑005),
  - Number of generation failures,
  - Number of analysis failures,
  - Wall‑clock time (from `runtime_log.json`).  
- [ ] T035 [US3] Update `state.yaml` (via `code/update_state.py`) with SHA‑256 hashes for all new artefacts and a fresh `updated_at` timestamp.  

**Checkpoint** – Visual assets and the final run‑summary are ready for inclusion in the manuscript.

---

## Phase N – Polish & Cross‑Cutting Concerns

**Purpose**: Final cleanup, documentation, and quality‑of‑life improvements.

- [ ] T036a [P] Refresh `README.md` with an overview, installation steps, and the **N = 30 prompt** scope.  
- [ ] T036b [P] Populate `docs/quickstart.md` with a step‑by‑step guide to run the entire pipeline on the GitHub‑Actions runner.  
- [ ] T036c [P] Update `docs/research.md` with the finalized methodology, limitations, and a justification of the FPR‑correction approach.  
- [ ] T037a [P] Code cleanup – remove any unused imports across all modules in `code/`.  
- [ ] T037b [P] Run `black` (and `ruff` lint) across the repository to enforce formatting standards.  
- [ ] T037c [P] Add docstrings to every public function and class in `code/`.  
- [ ] T038 [P] Optimise model loading/unloading order to minimise peak RAM usage (e.g., load StarCoder, generate, unload, then load next model).  
- [ ] T039 [P] Add edge‑case unit tests in `tests/unit/` (e.g., empty prompt, unsupported language).  
- [ ] T040 [P] Harden the handling of generated code: ensure snippets are never executed, only written to disk and analysed statically.  
- [ ] T041 [P] Execute `quickstart.md` validation script to confirm the documentation matches the actual pipeline behaviour.  

---

### Dependencies & Execution Order

| Phase | Depends On |
|-------|------------|
| **Phase 0** | None (must be first) |
| **Phase 1** | Phase 0 |
| **Phase 2** | Phase 1 |
| **Phase 3** (US1) | Phase 2 |
| **Phase 4** (US2) | Phase 2 **and** successful completion of US1 (generation & raw findings) **and** manual calibration (T022b) |
| **Phase 5** (US3) | Phase 4 |
| **Polish** | All prior phases |

Within each user story, tasks marked `[P]` may run in parallel as long as their file targets do not overlap. Sequential dependencies are explicitly noted in the descriptions.

---
