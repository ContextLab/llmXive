---  
description: "Task list template for feature implementation"  
---  

# Tasks: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization  

**Input**: Design documents from `/specs/001-evaluating-code-summarization-bug-localization/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`  

**Tests**: Tests are OPTIONAL – include them only if explicitly requested in the feature specification.  

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

## Format  
```
- [ ] T### [P] [USx] <description> – <file path>
```  
- **[P]** – task can run in parallel (different files, no dependencies)  
- **[USx]** – user‑story label (e.g., US1, US2, US3)  

---

## Phase 0: Offline Pre‑processing (Manual – not run in CI)

**Purpose**: One‑time manual steps that require GPU resources or scope‑reduction documentation.

- [X] T000 [P] **Scope‑reduction documentation** – create `docs/scope_reduction.md` documenting that simulation replaces the human‑subject study only for CI, while the real‑study path remains supported. – `docs/scope_reduction.md`  

- [ ] T014‑real [Manual] **Generate real LLM summaries** – run `code/generation/run_gpu_summaries.py` (CUDA, 8‑bit quantisation) to produce `data/summaries/llm_summaries_real.csv`. Includes fallback to rule‑based summaries on timeout/empty output. – `code/generation/run_gpu_summaries.py`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 **Create project skeleton** – create directories `code/`, `data/`, `tests/`, `.github/`, `docs/`, `state/projects/PROJ-140‑evaluating‑the‑efficacy‑of‑code‑summarization‑bug‑localization`. – *multiple directories*  

- [ ] T002 [P] **Initialize Python environment** – add `requirements.txt` with `pandas`, `scikit‑learn`, `statsmodels`, `requests`, `datasets`, `srcml`, `numpy`, `matplotlib`, `linearmodels`. – `requirements.txt`  

- [ ] T003 [P] **Configure linting/formatting** – set up `ruff` and `black` configuration files. – `.ruff.toml`, `pyproject.toml`  

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before any user‑story work begins.

- [X] T004 **Create data directory hierarchy** – `data/raw/defects4j`, `data/processed`, `data/summaries`, `data/interaction_logs`, `data/analysis_results`, `data/consent`. – `data/`  

- [X] T005 [P] **Artifact‑hash utility** – implement `code/utils/hash_artifacts.py` (SHA‑256 hashes for versioning). – `code/utils/hash_artifacts.py`  

- [X] T006 [P] **Environment configuration** – create `.env` (paths, random seeds). – `.env`  

- [X] T007 **Base data models** – define `Participant`, `Task`, `Summary`, `AnalysisResult` in `code/utils/models.py`. – `code/utils/models.py`  

- [X] T008 **Logging infrastructure** – implement `code/utils/logging_utils.py` with PII‑scrubbing. – `code/utils/logging_utils.py`  

- [X] T009 [P] **CI resource monitor** – implement `code/utils/resource_monitor.py` to assert ≤7 GB RAM and ≤6 h runtime. – `code/utils/resource_monitor.py`  

- [X] T010 [P] **CLI entry point** – create `code/main.py` that orchestrates the pipeline and integrates the startup gate. – `code/main.py`  

- [X] T011 [P] **Defects4J downloader & stratified sampler** – implement `code/download/download_defectsj.py` to stream the dataset, extract a stratified sample of 20 buggy methods per project (Chart, Time, Math) → total 60, and write `data/raw/defects4j/ground_truth.csv`. Fails loudly on download errors. – `code/download/download_defectsj.py`  

- [X] T012 **Missing‑ground‑truth handler** – extend the downloader to flag tasks lacking `ground_truth_line` and write `data/interaction_logs/missing_ground_truth.json`. – `code/download/download_defectsj.py`  

- [X] T013 [P] **Prevent raw log commits** – add `.gitignore` entry for `data/interaction_logs/raw_logs*.csv` and a pre‑commit hook (`code/utils/prevent_raw_commit.py`) that scans for PII patterns. – `code/utils/prevent_raw_commit.py`  

- [X] T014 [P] **Generate simulated summary artifacts** – script `code/generation/generate_summaries_offline.py` creates `data/summaries/llm_summaries_sim.csv` (mock text) and `data/summaries/rule_summaries.csv` (rule‑based extracts). – `code/generation/generate_summaries_offline.py`  

---

## Phase 3: User Story 1 – Human‑Subject Study Data Collection (Priority P1)

**Goal**: Collect (or simulate) interaction logs for all three summary conditions.

**Independent Test**: Simulate a full cohort and verify the CSV contains valid timestamps, line selections, participant IDs, and condition labels.

- [X] T015 [P] **Latency calibrator unit test** – `code/tests/test_latency_calibrator.py`. – `code/tests/test_latency_calibrator.py`  

- [X] T016 [P] **Defects4J download unit test** – `code/tests/test_defects4j_download.py`. – `code/tests/test_defects4j_download.py`  

- [X] T017 [US1] **Latency calibration script** – `code/simulation/latency_calibrator.py` measures loopback latency; exits with code 1 if > 100 ms. – `code/simulation/latency_calibrator.py`  

- [X] T018 [US1] **Startup gate integration** – modify `code/main.py` to invoke the calibrator before any other work; abort on failure. – `code/main.py`  

- [ ] T019 [US1] **Latin‑square assignment generator** – `code/simulation/assignment_generator.py` creates balanced task assignments for 12 participants × 30 tasks. – `code/simulation/assignment_generator.py`  

- [ ] T020 [US1] **Baseline condition simulator** – `code/simulation/participant_sim_base.py` generates rows with `condition='baseline'`, null summary, realistic timestamps, and correct ground‑truth lines. – `code/simulation/participant_sim_base.py`  

- [ ] T021 [US1] **LLM‑condition simulator** – `code/simulation/participant_sim_llm.py` loads either `llm_summaries_sim.csv` (CI) or `llm_summaries_real.csv` (real mode) with fallback to `rule_summaries.csv`; produces interaction rows. – `code/simulation/participant_sim_llm.py`  

- [ ] T022 [US1] **Rule‑based condition simulator** – `code/simulation/participant_sim_rule.py` loads `rule_summaries.csv` and generates interaction rows. – `code/simulation/participant_sim_rule.py`  

- [ ] T023 [Manual] **Real‑subject data collector** – `code/simulation/participant_sim_real.py` runs the secure web‑form study, invoking the latency calibrator before start; writes `data/interaction_logs/raw_logs_real.csv`. – `code/simulation/participant_sim_real.py`  

- [ ] T024 [US1] **Dropout handling logic** – augment `code/simulation/participant_sim.py` to flag incomplete participant data (partial task sets) in `data/interaction_logs/dropout_flags.json`. – `code/simulation/participant_sim.py`  

- [ ] T025 [US1] **Anonymization script** – `code/utils/anonymize_logs.py` reads raw logs (simulated or real) and writes `data/interaction_logs/anonymized_logs.csv` with hashed participant IDs. – `code/utils/anonymize_logs.py`  

- [ ] T026 [US1] **Consent & secure storage** – `code/utils/secure_storage.py` creates `data/consent/`, adds it to `.gitignore`, sets `chmod 600`, and verifies it is absent from git history. – `code/utils/secure_storage.py`  

---

## Phase 4: User Story 2 – Statistical Analysis Pipeline (Priority P2)

**Goal**: Compute accuracy, speed, effect sizes, confidence intervals, and perform sensitivity analysis.

**Independent Test**: Feed a synthetic CSV and verify that p‑values, odds‑ratios, Cohen’s d, and 95 % CIs are produced for all four comparisons.

- [X] T027 [P] **McNemar unit test** – `code/tests/test_statistics.py`. – `code/tests/test_statistics.py`  

- [X] T028 [P] **LME & bootstrap unit test** – `code/tests/test_bootstrap_utils.py`. – `code/tests/test_bootstrap_utils.py`  

- [X] T029 [US2] **Sensitivity‑range config** – `code/analysis/config.py` defines `SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.10]`. – `code/analysis/config.py`  

- [X] T030 [US2] **Outlier detection** – `code/analysis/run_statistics.py` flags tasks with duration > 30 min and writes `data/analysis_results/outlier_flags.json`. – `code/analysis/run_statistics.py`  

- [X] T031 [US2] **Outlier exclusion** – same module filters participants with ≥ 2 outliers; writes cleaned logs to `data/interaction_logs/cleaned_logs.csv`. – `code/analysis/run_statistics.py`  

- [X] T032 [US2] **Data loader** – `code/analysis/load_data.py` reads `cleaned_logs.csv`, summary files, and `missing_ground_truth.json`; returns tidy DataFrames. – `code/analysis/load_data.py`  

- [X] T033 [US2] **Bootstrap utilities** – `code/analysis/bootstrap_utils.py` implements cluster bootstrap (fixed seed) for Odds Ratios and Cohen’s d with CI computation. – `code/analysis/bootstrap_utils.py`  

- [X] T034 [US2] **Multiple‑comparison correction** – `code/analysis/correction_utils.py` applies Holm‑Bonferroni at α = 0.05. – `code/analysis/correction_utils.py`  

- [X] T035 [US2] **Statistical test runner** – `code/analysis/run_statistics.py` performs:  
  * McNemar tests (baseline vs LLM, baseline vs rule)  
  * Linear Mixed‑Effects models for time‑to‑decision (random intercepts per participant)  
  * Effect‑size calculations (Odds Ratio, Cohen’s d) with bootstrapped 95 % CIs  
  * Holm‑Bonferroni correction  
  * Writes `data/analysis_results/results.csv`. – `code/analysis/run_statistics.py`  

- [X] T036 [US2] **Results report generator** – `code/analysis/generate_report.py` creates `data/analysis_results/final_report.md` summarising metrics, significance flags, and effect‑size interpretation. – `code/analysis/generate_report.py`  

- [X] T037 [US2] **Sensitivity‑analysis sweep** – `code/analysis/run_sensitivity.py` loops over thresholds from `config.py`, re‑runs statistics, and writes `data/analysis_results/sensitivity_analysis.csv`. – `code/analysis/run_sensitivity.py`  

- [X] T038 [US2] **Sensitivity‑analysis report** – `code/analysis/generate_sensitivity_report.py` produces `data/analysis_results/sensitivity_analysis_report.md` with a line‑plot (`sensitivity_plot.png`). – `code/analysis/generate_sensitivity_report.py`  

---

## Phase 5: User Story 3 – Reproducibility Package Generation (Priority P3)

**Goal**: Assemble a self‑contained, OSF‑ready package that can be rerun on GitHub Actions free‑tier.

**Independent Test**: Clone the OSF repository, trigger the CI workflow, and confirm that results match the reference hash within tolerance.

- [X] T039 [P] **CI reproducibility workflow** – `.github/workflows/test_reproducibility.yml` installs dependencies, runs `code/main.py`, enforces ≤6 h / ≤7 GB limits via `resource_monitor`, and compares current `results.csv` hash against `data/reproducibility_ref.json` (tolerance = 1e‑4). – `.github/workflows/test_reproducibility.yml`  

- [X] T040 [P] **Reproducibility test script** – `code/tests/test_reproducibility.py` re‑runs the analysis with the same seed and asserts numerical tolerance. – `code/tests/test_reproducibility.py`  

- [X] T041 [US3] **PII‑removal verifier** – `code/utils/verify_pii_removal.py` scans `anonymized_logs.csv` for email/IP patterns and ensures `data/consent/` is absent from git history. – `code/utils/verify_pii_removal.py`  

- [X] T042 [US3] **Package builder** – `code/utils/package_reproducibility.py` creates `data/reproducibility_package_v1.0.tar.gz` containing source code, results, anonymized logs, `docs/README.md`, `requirements.txt`, and `state/projects/.../artifact_hashes.yaml`; excludes raw logs and consent data. – `code/utils/package_reproducibility.py`  

- [X] T043 [US3] **Artifact‑hash manifest** – `code/utils/update_hashes.py` generates `state/projects/PROJ-140‑.../artifact_hashes.yaml` with SHA‑256 hashes for all packaged files. – `code/utils/update_hashes.py`  

- [X] T044 [US3] **README for OSF package** – write `docs/README.md` describing how to rerun the analysis on GitHub Actions free‑tier (≤6 h, ≤7 GB RAM, no GPU). – `docs/README.md`  

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T045 [P] **Documentation updates** – enrich `docs/README.md` with installation steps, dependency list, and execution examples. – `docs/README.md`  

- [X] T046 [P] **API documentation** (if applicable) – create `docs/api.md` or remove if not needed. – `docs/api.md`  

- [X] T047 [P] **Code cleanup – logging utils** – remove unused imports from `code/utils/logging_utils.py`. – `code/utils/logging_utils.py`  

- [X] T048 [P] **Code cleanup – data models** – simplify structures in `code/utils/models.py`. – `code/utils/models.py`  

- [X] T049 [P] **Performance optimisation – analysis** – ensure `run_statistics.py` stays < 6 GB RAM and < 5 h runtime on the CI runner. – `code/analysis/run_statistics.py`  

- [X] T050 [P] **Additional unit tests – edge cases** – add tests in `code/tests/test_statistics.py` for missing ground‑truth and dropout scenarios. – `code/tests/test_statistics.py`  

- [X] T051 [P] **Data‑integrity tests** – `code/tests/test_data_integrity.py` validates schema of all CSV/JSON artifacts. – `code/tests/test_data_integrity.py`  

- [X] T052 [P] **Secure logging** – extend `logging_utils.py` with regex‑based PII scrubber (already present). – `code/utils/logging_utils.py`  

- [X] T053 [P] **Streaming‑chunk documentation** – update docstring in `code/download/download_defectsj.py` to state chosen chunk size and online‑statistics strategy. – `code/download/download_defectsj.py`  

---  

**Dependencies & Execution Order**

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Story 1 (Phase 3)** → **User Story 2 (Phase 4)** → **User Story 3 (Phase 5)** → **Polish (Phase N)**.  

- Parallelizable tasks marked `[P]` may be executed concurrently provided their file paths do not overlap.  

- Manual tasks (`[Manual]`) are performed offline and are not part of the CI dependency graph.  

---  

*All tasks follow the canonical “‑ [ ] T### [P] [USx] description – file path” format, include explicit file locations, and respect the data‑flow ordering required by the specification.*
