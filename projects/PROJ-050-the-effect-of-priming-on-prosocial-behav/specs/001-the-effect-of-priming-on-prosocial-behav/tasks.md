# Tasks: The Effect of Priming on Prosocial Behavior in Online Communities

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts in `specs/001-the-effect-of-priming-on-prosocial-behav/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`

---

## Phase 1 – Project bootstrap (already completed)

- [~] T001 Establish the project directory layout under `projects/PROJ-050-the-effect-of-priming-on-prosocial-behav/`.
- [X] T002 Initialize a Python 3.11 environment; pin dependencies in `code/requirements.txt` (pandas, numpy, scikit‑learn, statsmodels, vaderSentiment, datasets, pyyaml, hashlib, tqdm).
- [X] T003 Document the runnable entry‑point command in `quickstart.md` (e.g., `python -m pipeline.run`).

---

## Phase 2 – Core infrastructure (already completed)

- [~] T004 [P] Create data folders: `data/raw/`, `data/processed/`, `data/validation/`, `data/results/`.
- [X] T005 [P] Implement a checksum utility (`code/utils/checksum.py`) for raw‑data integrity verification.
- [X] T006 [P] Implement schema‑validation helpers (`code/utils/schema_validator.py`) for `dataset.schema.yaml`, `scored.schema.yaml`, and `model_results.schema.yaml`.
- [X] T007 [P] Add a simple configuration module (`code/config.py`) exposing `TARGET_N`, dataset identifiers, and output directories via environment variables.
- [X] T008 Implement project‑wide logging (`code/utils/logger.py`) that writes to a per‑process log file (e.g., `logs/run_<pid>.log`) to avoid race conditions.
- [X] T009 Add a pytest configuration (`pytest.ini`) and create the test hierarchy `tests/unit/`, `tests/integration/`, `tests/contract/`.

---

## Phase 3 – Data‑fit resolution & ingestion (US 1)

- [X] T010 [US1] **Identify and secure a public Reddit dataset that includes thread titles** (e.g., a full Pushshift dump via the `pushshift.io` API or an HF dataset with a `title` field). Document the chosen source, URL/identifier, and access method in `docs/dataset_acquisition.md`. **If no such dataset exists, raise a project‑blocking issue** (FR‑001 cannot be satisfied without titles).
- [ ] T026 Acquire the title‑bearing Reddit dataset identified in T010 and record the source URL/identifier in `docs/dataset_acquisition.md`. <!-- FAILED-IN-EXECUTION: code/00_check_dataset.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/00_check_dataset.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/00_check_dataset.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/00_check_dataset.py exit=1 -->
- [ ] T011 [US1] Implement `code/01_ingest.py` to **stream** the acquired dataset, filter for subreddits `AskReddit`, `science`, `relationships`, compute `user_tenure` from `created_utc`, hash `author` with SHA‑256 → `user_id`, classify `thread_type` using regex `/(thank|help|support|care)/i` on the **thread title**, and write:
  - `data/processed/anonymized.csv` (conforms to `dataset.schema.yaml`, includes `thread_type` values “Prime” or “Control”)
  - `data/processed/raw_counts.json` (raw vs. processed comment counts, satisfies SC‑001)
  *The script aborts with a clear error if required fields (including `title`) are missing.*
- [ ] T012 [US1] **Create unit‑test suite for ingestion logic**:
  - `tests/unit/test_classification.py` – verifies regex‑based `thread_type` assignment on synthetic titles.
  - `tests/unit/test_anonymization.py` – checks SHA‑256 hashing of `author`, ensures `created_utc` does not appear in the output CSV, and validates `user_tenure` calculation.
- [ ] T027 (no‑op) Previously added test files are now covered by T012; retain for traceability.
- [ ] T028 (no‑op) Previously added test files are now covered by T012; retain for traceability.

---

## Phase 4 – Sentiment & prosocial scoring (US 2)

- [ ] T013 [US2] Conduct the **CPU feasibility analysis** required by FR‑002c. Write `docs/feasibility_report.md` summarising expected runtime, peak RAM, and confirming that the VADER + lexicon pipeline comfortably fits the free‑CPU runner. If infeasible, record a “FR‑002c Deferred” note in the same file.
- [ ] T014 [US2] Implement `code/02_score.py` to:
  * Load `data/processed/anonymized.csv`.
  * Compute VADER sentiment components (`compound`, `pos`, `neu`, `neg`).
  * Count occurrences of prosocial keywords from `distinct_prosocial_lexicon.txt` (explicitly **excluding** the prime words `thank`, `help`, `support`, `care`).
  * Add `thread_length` (character count of `body`).
  * Write `data/processed/scored.csv` matching `scored.schema.yaml`.
- [ ] T015 [US2] Create a **human‑annotation collection script** (`code/validation/collect_human_annotations.py`) that randomly samples 200 rows from `scored.csv`, writes `comment_id`, generated `rater_id` (e.g., `rater_1`, `rater_2`) and placeholder `label_prosocial_intent` columns to `data/validation/gold_standard.csv` (conforms to `gold_standard.schema.yaml`), and prints instructions for dual‑blind raters. The script is deterministic (`seed = 42`) and records the sampling summary in `data/validation/sampling_log.json`.
- [ ] T016 [US2] Implement `code/validation/run_validation.py` to:
  * Load `data/processed/scored.csv` and `data/validation/gold_standard.csv`.
  * Compute **Cohen’s Kappa** for the prosocial keyword classification and **Pearson r** between VADER `compound` and the human binary label.
  * Write `results/validation_report.json` containing `kappa`, `pearson_r`, and a flag `simulated: false`.
  * Abort with a clear error if the gold‑standard file is missing.

---

## Phase 5 – Statistical analysis (US 3)

- [ ] T017 [US3] Fit the Linear Mixed Model using `statsmodels` `MixedLM` with the formula  
  `prosocial_intent_score ~ thread_type + thread_length + user_tenure + (1|subreddit) + (1|user_id)` (requires `thread_type` from T011).  
  * Verify convergence (`model.converged == True`).  
  * Record the p‑value for `thread_type`.  
  * Export `data/results/model_results.json` (conforms to `model_results.schema.yaml`).  
  * Generate a PNG of the prosocial‑intent distribution (`data/results/prosocial_distribution.png`).
- [ ] T018 [US3] **Sensitivity analysis**: re‑fit the model with optimizer tolerances `1e‑4`, `1e‑5`, `1e‑6`; capture each run’s convergence flag and `thread_type` p‑value; append these records to the `sensitivity_analysis` array in `model_results.json`.
- [ ] T019 [US3] **Fallback descriptive analysis** – If after acquisition the total comment count is insufficient for the LMM (e.g., < 4 000 per group), run `code/03_descriptive.py` to compute:
  * Mean, median, SD of `prosocial_intent_score` per subreddit.
  * Correlation of `thread_length` and `prosocial_intent_score`.
  * Export `data/results/descriptive_summary.json` and a bar‑plot PNG (`data/results/subreddit_prosocial.png`).  
  * Include `"thread_type_available": false` in the JSON so reviewers know the primary hypothesis could not be tested.
- [ ] T032 Generate a **placeholder model results** JSON (`data/results/model_results.json`) that conforms to `model_results.schema.yaml` with `convergence_status: "failed"` and a minimal PNG (`data/results/prosocial_distribution.png`) when the LMM cannot be fitted for any reason, ensuring SC‑005 is always satisfied.

---

## Phase 6 – Reproducibility hand‑off & verification

- [ ] T020 Write a concise **methods & results** hand‑off (`paper/methods_results.md`) that:
  * Lists each pipeline stage, the exact file paths of its outputs, and the verification metrics (raw counts, Kappa, Pearson r, LMM convergence, p‑values, or descriptive stats).
  * Clearly notes any deferred requirements (e.g., FR‑001 or FR‑003) **only if acquisition truly fails**; otherwise, all mandatory FRs are satisfied.
- [ ] T021 [US3] Add an **integration test** (`tests/integration/test_full_pipeline.py`) that runs the whole pipeline on a tiny sampled slice of the dataset (e.g., first 10 000 streamed rows) and asserts that:
  * `data/processed/anonymized.csv` and `data/processed/scored.csv` exist and pass schema validation.
  * `results/validation_report.json` contains both `kappa` and `pearson_r`.
  * `data/results/model_results.json` exists and conforms to its schema (no OR condition).
- [ ] T022 Update `quickstart.md` (already created in Phase 1) to include the one‑line command that triggers the full pipeline (`python -m pipeline.run`) and a note pointing to `tests/integration/test_full_pipeline.py` for CI verification.

---

## Phase 7 – Polish & documentation (optional but recommended)

- [ ] T023 Review all contract‑validation utilities to ensure they raise informative errors when schema mismatches occur, and add a unit‑test suite (`tests/unit/test_utils_validation.py`) verifying error messages.
- [ ] T024 Add a `README.md` at the project root summarising the research question, data sources, and how to reproduce each major result.
- [ ] T025 Ensure all generated PNGs are stored under `figures/` (symlinked from `data/results/` if needed) to match the platform’s artefact‑tracking conventions.
- [ ] T029 Set a global random seed (`random.seed(42)` and `np.random.seed(42)`) in a shared utility (`code/utils/seed.py`) and have all pipeline scripts import it at start, satisfying reproducibility (Constitution Principle I).

### Dependency & execution order summary

| Task | Depends on |
|------|------------|
| T010 | – |
| T026 | T010 |
| T011 | T026 |
| T012 | T011 |
| T027 | T012 (no‑op) |
| T028 | T012 (no‑op) |
| T013 | – |
| T014 | T011, T012 |
| T015 | T014 |
| T016 | T014, T015 |
| T017 | T014, T016 |
| T018 | T017 |
| T019 | T014 (fallback) |
| T032 | T017 (fallback when needed) |
| T020 | T017 or T019 |
| T021 | All pipeline tasks (T014‑T018, T019) |
| T022 | T021 |
| T023 | – |
| T024 | – |
| T025 | – |
| T029 | – (utility imported by all scripts) |

--- 

*All tasks write only to project‑owned paths (`code/`, `data/`, `results/`, `docs/`, `tests/`, `paper/`, `figures/`). No platform‑state files are touched. The pipeline is fully CPU‑first; no GPU resources are requested.*  