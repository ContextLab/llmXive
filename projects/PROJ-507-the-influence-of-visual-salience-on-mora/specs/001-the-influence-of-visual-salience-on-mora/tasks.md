---
description: "Task list for feature implementation"
---

# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: Design documents from `/specs/001-visual-salience-moral-judgments/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – include them only if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] T### [P?] [Story] Description (file path)`

- **[P]** – can run in parallel (different files, no dependencies)  
- **[Story]** – which user story this task belongs to (e.g., US1, US2, US3)  
- Include exact file paths in the description.

## Path Conventions

- **Single‑project layout**: `code/`, `tests/`, `data/` at repository root  
- Adjust if a different layout is adopted.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [ ] T001a Create project directory structure (`code/`, `data/raw/`, `data/processed/`, `data/survey/`, `data/synth/`, `tests/`, `contracts/`, `config/`, `docs/`).  
  **Verification**: Implement `code/verify_structure.py` that asserts all directories exist.  
- [ ] T001b-INIT [P] Generate missing config files (`.gitignore`, `.ruff.toml`, `.env.example`).  
  - Write `.gitignore` excluding `data/`, `__pycache__/`, `*.pyc`.  
  - Write `.ruff.toml` with `max-line-length = 100`.  
  - Write `.env.example` containing `VISUAL_GENOME_URL` and `SURVEY_API_KEY`.  
  - Verify with the script created in T001a.  
- [ ] T001c [P] Create `config/pre_registration.yaml` with a placeholder `MIN_PRECISION: <value_to_be_set_by_researcher>` and `verification_status: UNVERIFIED`.  
- [ ] T002 Initialize Python project with `requirements.txt` (e.g., `numpy`, `pandas`, `scipy`, `statsmodels`, `Pillow`, `requests`, `matplotlib`, `seaborn`, `opencv-python-headless`, `streamlit`, `torch`, `transformers`, `ordinal`, `ordinal-mixed-models`).  
- [ ] T003a [P] Verify `.ruff.toml` exists and is syntactically valid.  
- [ ] T008a [P] Verify `.env.example` exists and contains the required keys (`VISUAL_GENOME_URL`, `SURVEY_API_KEY`).  

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before any user story can begin.

- [ ] T004 [P] Implement reproducibility helper `code/config.py` with `seed_everything(seed=42)` that seeds `numpy`, `random`, and `torch`.  
- [ ] T005 [P] Implement data‑integrity verification script `code/verify_data_integrity.py`.  
- [ ] T006 [P] Set up basic logging configuration in `code/logging_config.py`.  
- [ ] T007 [P] Create base data‑model classes in `code/models.py`: `Scenario`, `StimulusVariant`, `Response`, `Participant` (all attributes per spec). Ensure any stochastic defaults call `seed_everything()`.  
- [ ] T052 [P] Implement a strict “fail loudly” data loader in `code/data_prep.py` that raises `DataFetchError` on any real‑fetch failure (no silent synthetic fallback).  
- [ ] T052-VERIFY-AND-FIX [P] Verify the behavior of T052 by simulating a network failure; automatically patch `code/data_prep.py` if it does not raise `DataFetchError`.  
- [ ] T053-RAW-CHECKSUM [P] Download the full Visual Genome dataset from its canonical Hugging‑Face source, compute a SHA‑256 checksum, and store it in `data/raw/source_checksum.txt`. Verify the checksum matches the published hash.  
- [ ] T053-GEN [P] Generate a deterministic list of 1 000 image IDs (`data/raw/selected_ids.json`) using a fixed seed (42) derived from the verified source.  
- [ ] T053-EXEC [P] Download only the images whose IDs appear in `selected_ids.json` (using `datasets.load_dataset("visual_genome", split="train", streaming=False)`), compute per‑image SHA‑256 checksums, and store metadata in `data/raw/sample_metadata.json`.  
- [ ] T053c [P] Verify that `selected_ids.json` exists before any downstream task runs; raise `FileNotFoundError` if missing.  
- [ ] T053b [P] Add reproducibility verification in `code/data_prep.py` that re‑downloads the subset and checks against `sample_metadata.json`; raise `ReproducibilityError` on mismatch.  
- [ ] T054 [P] Implement “verified source” injection in `code/data_prep.py`: if environment variable `VERIFIED_DATA_SOURCE` is set, use that single source (e.g., `huggingface_hub.hf_hub_download`) and ignore other URLs.  
- [ ] T055 [P] Add unit test `tests/unit/test_data_loader.py` that simulates a network failure and asserts `DataFetchError` is raised (no synthetic data returned).  
- [ ] T055a [P] Run the test from T055 and verify it passes.  
- [ ] T056 [P] Add unit test `tests/unit/test_data_cleaning.py` that checks the straight‑lining detection routine correctly excludes participants with variance < 0.1 or > 90 % identical ratings.  

*Checkpoint*: Foundational work complete – user‑story implementation may now begin.

---

## Phase 3: User Story 1 – Data Preparation & Salience Manipulation (Priority P1)

**Goal**: Ingest open visual datasets, identify morally ambiguous images, and generate low/medium/high salience variants while preserving semantics.

**Independent Test**: Run the pipeline on a subset of raw images; verify (1) metadata filter, (2) human‑coding reliability (Cohen κ ≥ 0.6), (3) RMS‑contrast change, and (4) CLIP similarity ≥ 0.95 plus ≥ 80 % coder agreement on narrative preservation.

### Implementation Tasks

- [ ] T013 [US1] Implement dataset ingestion in `code/data_prep.py`: fetch Visual Genome (primary) or MoralD (secondary) from the verified source, filter for `social`/`conflict` tags, and output `data/processed/stimuli_raw.csv`.  
- [ ] T013-SOURCE-VERIFY [US1] Verify that the source used matches the checksum recorded in T053-RAW-CHECKSUM; raise `SourceMismatchError` if they differ.  
- [ ] T013b [US1] Download the external validation resource (e.g., MoralD) into `data/raw/external_validation/`.  
- [ ] T014-FILTER [US1] Implement metadata filtering (tags `social`, `conflict`) in `code/data_prep.py`; output `data/processed/candidates_filtered.csv`.  
- [ ] T014-CROSSREF-EXEC [US1] Perform cross‑reference verification against the external validation source (from T013b); log results in `data/processed/cross_reference_log.txt`; raise `CrossReferenceError` on failure.  
- [ ] T015d [US1] Implement the human‑coding protocol in `code/human_coding.py`: recruit ≥ 3 annotators, collect 5‑point ambiguity ratings, compute mean scores and Cohen’s κ, and output `data/processed/valid_scenarios.csv`.  
- [ ] T015e-RECRUIT [US1] Generate a recruitment survey (Qualtrics/Prolific) via `code/generate_human_coding_survey.py`.  
- [ ] T015e-WAIT [US1] Poll `data/raw/human_coding/` until ≥ 3 valid annotator files are present.  
- [ ] T015a [US1] Create a unit‑test harness in `code/human_coding.py` that generates mock annotation data (`data/raw/human_coding/mock_annotations.csv`) for CI purposes only.  
- [ ] T015a1 [US1] Verify that mock annotation files live only under `data/raw/human_coding/` and never leak into `data/processed/`.  
- [ ] T015b [US1] Add unit test `tests/unit/test_human_coding.py` that validates `calculate_cohens_kappa` on the mock data.  
- [ ] T015c [US1] Execute the real human‑coding pipeline: read actual annotator files, compute κ, filter scenarios (mean ≥ 3.5 & κ ≥ 0.6), and write `data/processed/valid_scenarios.csv`.  
- [ ] T016a [US1] Write the versioned manipulation configuration file `config/manipulation.yaml` (fields: `version`, `seed`, `luminance_levels`, `target_region`, `output_path`).  
- [ ] T016 [US1] Implement salience manipulation (low/medium/high luminance) in `code/data_prep.py` using parameters from `config/manipulation.yaml`; output manipulated images to `data/processed/images/` and manifest `data/processed/stimuli_manipulated.csv`.  
- [ ] T017 [US1] Implement semantic‑preservation verification in `code/validation.py` (CPU‑only CLIP):  
  - Compute ROI embeddings for original vs. manipulated; require cosine similarity ≥ 0.95.  
  - Compute background similarity ≥ 0.99.  
  - Verify texture/edge‑density change < 0.05 (Laplacian variance).  
- [ ] T017-CPU-OPT [US1] Optimize CLIP inference in `code/validation.py` with `torch.no_grad()` and batch processing to stay < 2 GB RAM.  
- [ ] T018 [US1] Add failure logging and exclusion logic in `code/data_prep.py` for images where manipulation or verification fails.  
- [ ] T019b-RECRUIT [US1] Create a recruitment survey for the pilot manipulation‑check coder panel (`code/generate_manipulation_check_survey.py`).  
- [ ] T019b-WAIT [US1] Poll `data/raw/manipulation_check/` until ≥ 3 valid coder responses are present.  
- [ ] T019-EXEC [US1] Run the manipulation‑check analysis: compute coder agreement on narrative preservation; if < 80 % flag scenario as failed and exclude it. Store results in `data/processed/narrative_check_validated.csv`.  
- [ ] T019a [US1] Generate the final stimulus manifest `data/processed/stimulus_manifest.json` linking `scenario_id`, `variant_id`, `salience_level`, and a `source_type` field (`real` | `synthetic`).  
- [ ] T016b [US1] Create the stimulus contract schema `contracts/stimulus.schema.yaml` describing the JSON manifest structure.  

*Checkpoint*: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 – Survey Deployment & Data Collection (Priority P2)

**Goal**: Present the manipulated images in a within‑subject design, randomize order, and log blame ratings.

**Independent Test**: Run a pilot survey with a small cohort; verify randomization, logging of participant ID, image ID, salience level, and rating.

### Implementation Tasks

- [ ] T022 [US2] Implement the randomization engine (`code/survey_sim.py`) that generates per‑participant sequences respecting: no identical scenarios consecutively, balanced salience order, and no repeat of the same salience level for a scenario.  
- [ ] T023a [US2] Implement a pilot‑only simulation interface (`code/survey_deploy.py`) that writes synthetic sequences to `data/synth/survey_sequences.json`. (For CI only – never used for real data.)  
- [ ] T023a1 [US2] Verify that the synthetic file lives under `data/synth/` and not under `data/survey/`.  
- [ ] T023c [US2] Generate the production survey configuration `config/survey_api.yaml` (placeholders for Prolific/Qualtrics keys) and the deployment script `code/survey_deploy_production.py` that renders the survey, enforces within‑subject constraints, and logs responses to `data/survey/real_responses.csv`.  
- [ ] T023b [US2] Integrate the production script into a Streamlit app (`code/survey_deploy.py`).  
- [ ] T024 [US2] Implement the response‑logging handler (`code/response_logger.py`) that appends each valid response (participant ID, stimulus ID, salience, rating, timestamp) to `data/survey/real_responses.csv`.  
- [ ] T024c-IMPL [US2] Write `scripts/generate_prolific_link.py` that deterministically creates the recruitment link for the chosen platform.  
- [ ] T024c [US2] Run the script from T024c-IMPL to produce the link and store it in `data/survey/prolific_link.txt`.  
- [ ] T024c-VERIFY [US2] Execute a mock survey session using the generated link to confirm that within‑subject constraints are enforced and that responses are written to `data/survey/mock_responses.csv`.  
- [ ] T024b [US2] Execute the real survey deployment (or mock mode for local verification) via `code/survey_deploy_production.py`; output either `data/survey/mock_responses.csv` (mock) or `data/survey/real_responses.csv` (real).  
- [ ] T026 [US2] Implement a pilot‑data simulation script (`code/survey_sim.py`) that generates synthetic blame ratings for n ≥ 20 participants; write to `data/synth/pilot_responses_sim.csv`. (CI only.)  
- [ ] T026a [US2] Ensure strict separation: `data/survey/` contains only real (or mock) survey data; `data/synth/` contains only synthetic data. Raise `DataHygieneError` on violation.  
- [ ] T023e [US2] Create the response contract schema `contracts/response.schema.yaml` defining required fields (`participant_id`, `stimulus_id`, `salience_level`, `rating`, `timestamp`).  

### Tests (Restored)

- [ ] T020 [P] [US2] Unit test `tests/unit/test_survey_logic.py` to verify the randomization engine respects within‑subject constraints.  
- [ ] T021 [P] [US2] Unit test `tests/unit/test_data_schema.py` to validate that logged rows conform to `contracts/response.schema.yaml`.  
- [ ] T022 [P] [US2] Integration test `tests/integration/test_survey_flow.py` that runs the full pilot‑simulation pipeline and checks end‑to‑end logging.  

*Checkpoint*: User Stories 1 & 2 are independently functional.

---

## Phase 5: User Story 3 – Statistical Analysis & Reporting (Priority P3)

**Goal**: Fit a Cumulative Link Mixed Model (CLMM), apply robust corrections, compute effect sizes, perform power analysis, and generate a final report.

**Independent Test**: Run the full analysis on a synthetic dataset with a known injected effect (β = 0.5) and verify that the pipeline detects the effect, reports correct odds ratios, and respects convergence/fallback logic.

### Implementation Tasks

- [ ] T036 [US3] Implement a pipeline‑validation script (`code/validation.py`) that injects a synthetic effect into a generated dataset and runs the full analysis to confirm correct detection before any real data are processed.  
- [ ] T045 [US3] Execute data‑cleaning (`code/data_cleaning.py`) on the real survey file (`data/survey/real_responses.csv`) to remove straight‑liners (variance < 0.1 OR > 90 % identical ratings); output `data/processed/cleaned_responses.csv`.  
- [ ] T045‑SYNTH [US3] Run the same cleaning routine on `data/synth/pilot_responses_sim.csv` and output `data/processed/cleaned_responses_synth.csv`.  
- [ ] T045b [US3] During cleaning, add an `is_real_data` flag to each row (True for real, False for synthetic).  
- [ ] T032a [US3] Implement convergence‑check logic in `code/analysis.py`: function `check_convergence_and_fallback(model)` that returns the primary model if `model.converged` else switches to a fallback (LMM with robust SE → Bootstrap CLMM). Record `convergence_status` and `fallback_reason`.  
- [ ] T032b [US3] Implement the fallback model functions (`fit_lmm_robust()`, `fit_bootstrap_clmm()`) in `code/analysis.py`, preserving random intercepts for Participant and Scenario where applicable.  
- [ ] T030‑IMPL [US3] Write the primary CLMM fitting code (`run_clmm_analysis()`) using the `ordinal` package: `Rating ~ Salience + (1|Participant) + (1|Scenario)`.  
- [ ] T031‑IMPL [US3] Write robustness‑check code (`run_robustness_checks()`) that, after a successful CLMM, performs bootstrap resampling; if CLMM fails, automatically invokes the fallback selected by T032a.  
- [ ] T030‑EXEC [US3] Execute the primary analysis on `data/processed/cleaned_responses.csv` (or the synthetic counterpart).  
- [ ] T031b [US3] Explicitly call `check_convergence_and_fallback` after T030‑EXEC; if a `ConvergenceError` is raised, run the appropriate fallback model and write results to `data/analysis/results_fallback.csv`.  
- [ ] T031‑EXEC [US3] Run the secondary robustness checks (bootstrap or fallback) on the cleaned dataset.  
- [ ] T034 [US3] Perform ordinal post‑hoc pairwise comparisons (Low vs Medium, Medium vs High, Low vs High) with Tukey adjustment for the primary CLMM; if a fallback model is used, apply Bonferroni correction. Store results in `data/analysis/posthoc_results.csv`.  
- [ ] T035 [US3] Compute effect sizes (odds ratios) and 95 % confidence intervals for the salience fixed effect; write to `data/analysis/effect_sizes.csv`.  
- [ ] T046 [US3] Load `MIN_PRECISION` from `config/pre_registration.yaml`; calculate the CI width for the salience coefficient and compare against the threshold. If the config is missing or `verification_status` = `UNVERIFIED`, raise `PreRegistrationError`. Append `ci_width`, `precision_adequate`, and `verification_status` to `data/analysis/results.json`.  
- [ ] T047 [US3] Perform post‑hoc power analysis (`code/power_analysis.py`) using the observed effect size; write `power_value` and `power_adequate` (True if ≥ 0.80) to `data/analysis/power_results.json`.  
- [ ] T047‑RECOVERY [US3] If `power_adequate` is False, generate a remediation plan (`data/analysis/adjustment_plan.md`) recommending additional participants or re‑run parameters.  
- [ ] T047b [US3] Merge `power_results.json` into `results.json` (add `power_value` and `power_adequate`).  
- [ ] T047c [US3] Ensure the final report generator (`code/analysis.py` – T037) reads the enriched `results.json` and includes power information.  
- [ ] T070 [US3] Power‑gate: before report generation, verify `power_adequate`. If False and no `adjustment_plan.md` exists, automatically create a default plan; then continue to report generation.  
- [ ] T037 [US3] Implement the final report generator (`code/report_generator.py`) that reads `data/analysis/results.json` and produces a human‑readable summary (Markdown or PDF) including model convergence status, effect sizes, CI widths, precision check outcome, and power assessment.  

### Tests (Optional)

- [ ] T027 [P] [US3] Unit test `tests/unit/test_analysis.py` to verify CLMM fitting on a synthetic dataset with a known β = 0.5.  
- [ ] T028 [P] [US3] Unit test `tests/unit/test_corrections.py` to validate Tukey‑adjusted and Bonferroni‑adjusted post‑hoc logic.  
- [ ] T029 [P] [US3] Unit test `tests/unit/test_metrics.py` to confirm odds‑ratio calculation matches manual computation.  
- [ ] T030 [P] [US3] Integration test `tests/integration/test_analysis_pipeline.py` that runs the entire analysis pipeline on synthetic data and checks that `results.json` contains the expected fields and values.  

*Checkpoint*: All three user stories are now independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T038a [P] Update `docs/paper_draft.md` – add **3.1 Methods** section describing the CLMM specification, data‑cleaning pipeline, and ordinal post‑hoc corrections.  
- [ ] T038b [P] Update `docs/paper_draft.md` – add **4.1 Results** section with placeholders for CLMM tables, effect sizes, CI widths, and power statements.  
- [ ] T039a [P] Refactor `code/data_prep.py` to reduce cyclomatic complexity < 10 (verify with `ruff`).  
- [ ] T039b [P] Refactor `code/analysis.py` to separate model fitting from result reporting (verify with `ruff`).  
- [ ] T050 [P] Add a profiling script `code/profile_pipeline.py` that measures runtime of each major stage (ingest, manipulation, survey, analysis).  
- [ ] T051a [P] Implement the profiler (record timestamps, write `data/analysis/runtime_log.txt`).  
- [ ] T051b [P] Run the profiler on the full dataset; store results.  
- [ ] T051c [P] If total runtime > 6 h, iteratively optimise `code/analysis.py` or `code/data_prep.py` until the limit is satisfied.  
- [ ] T040a [US3] In `code/analysis.py`, detect if the participant count falls below the planned minimum; if so, set `power_adequate = False` and append a warning about reduced power and wider CIs.  
- [ ] T040b [US3] Add unit test `tests/unit/test_power_edge_case.py` to verify the warning is triggered correctly for undersized samples.  
- [ ] T041a [P] Generate `quickstart.md` – a step‑by‑step guide covering environment setup, data download, pipeline execution, and result inspection.  
- [ ] T041b [P] Validate `quickstart.md` with a script that checks consistency against the task list; output validation log to `data/logs/quickstart_validation.txt`.  

---

## Phase 7: Review Resolution & Constitution Hardening (Revision Pass)

**Goal**: Address reviewer concerns about data integrity, reproducibility, and constitutional compliance.

- [ ] T065 [US1] Document the “Verified Source” injection mechanism in `docs/data_hygiene.md` (explain `VERIFIED_DATA_SOURCE` env‑var behavior).  
- [ ] T068 [US1] Add a “Real‑Data‑Only” gate in `code/analysis.py`: abort if `is_real_data` is False **and** `--allow-synthetic` is not supplied; raise `DataIntegrityError`.  
- [ ] T069 [US2] Add a similar “Real‑Data‑Only” gate in `code/survey_deploy.py`: abort deployment if the stimulus manifest’s `source_type` is `synthetic` without `--allow-synthetic`.  
- [ ] T071 [US1] In `code/human_coding.py`, enforce a check that at least 3 distinct annotator files are present before computing κ; raise `InsufficientAnnotatorsError` otherwise.  
- [ ] T072 [US3] Enhance `code/analysis.py` to log `convergence_status` and `fallback_reason` into `data/analysis/results.json` for full transparency.  

*Checkpoint*: All reviewer‑raised issues resolved; the pipeline is constitutionally compliant.

---
