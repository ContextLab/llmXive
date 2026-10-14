# Tasks: Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning  

**Inputs**: `spec.md`, `plan.md`, existing project artifacts, reviewer feedback.  

All paths are relative to the repository root.  

---  

## Phase 1 – Project Setup & Core Infrastructure  

- [ ] **T001** [​P​] Initialize project skeleton  
  - Create directories: `data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`.  
  - Add core files: `README.md` (one‑sentence description), `code/__init__.py`, `requirements.txt`, `tests/__init__.py`, `docs/README.md`.  
  - **Verification**: `tree` output shows all directories and files; `README.md` contains a one‑sentence project description.  

- [ ] **T001a** [​P​] Compute raw‑data checksums  
  - For each file under `data/raw/`, compute SHA‑256 checksum and write to `data/raw/checksums.sha256`.  
  - Record the manifest in project state YAML under `artifact_hashes`.  
  - **Verification**: Script `code/utils.py` provides `compute_checksums()`; after run, the manifest file exists and matches all raw files.  

- [ ] **T001b** [​P​] Pin random seeds for reproducibility  
  - Create `code/seed.py` that sets `numpy`, `random`, and `torch` (if present) seeds from a constant.  
  - Export `SEED = 42` and a helper `set_seed()` used by all stochastic scripts.  
  - **Verification**: Importing `code.seed` and calling `set_seed()` produces deterministic outputs; unit test confirms repeatability of a random number generation.  

- [ ] **T002** [​P​] Add Python 3.11 environment & dependencies  
  - File: `requirements.txt` (lists `scikit-learn`, `lightgbm`, `pandas`, `numpy`, `textstat`, `datasets`, `statsmodels`, `pytest`, `requests`).  
  - **Verification**: `pip install -r requirements.txt` succeeds on a clean runner.  

- [ ] **T003** [​P​] Configure linting & formatting  
  - Files: `pyproject.toml` (Black config) and `.ruff.toml` (Ruff config).  
  - **Verification**: `ruff check .` and `black --check .` both return no violations.  

- [ ] **T004** [​P​] Implement data loader & label check (`code/load_data.py`)  
  - Load public learning‑analytics datasets (ASSISTments, OULAD) via `datasets.load_dataset`.  
  - Verify required interaction columns (latency, error, hint, pause) **and** required timestamped response fields (`response_time_ms`, `timestamp`).  
  - Verify presence of concurrent load label column (e.g., `NASA_TLX`).  
  - If load labels are absent, emit **exact** warning:  
    ```
    Public dataset lacks concurrent load labels. Manual Golden Set (T007g) is required.
    ```  
  - **Verification**: Running `python -m code.load_data` prints the warning when appropriate and creates `data/processed/interactions.csv`.  

- [ ] **T005** [​P​] Create utility library (`code/utils.py`)  
  - Implement: VIF calculation, Flesch‑Kincaid scoring, Jaccard similarity, semantic similarity (TF‑IDF cosine), and `compute_checksums()` used by T001a.  
  - Export functions in `__all__`.  
  - **Verification**: Unit tests in `tests/unit/test_utils.py` pass (`pytest -q`).  

- [ ] **T006** [​P​] Generate Golden‑Set template (`data/processed/golden_set_template.csv`)  
  - Columns: `interaction_id`, `expert_load_score` (empty).  
  - Add accompanying README `docs/golden_set_creation.md` with labeling instructions.  
  - **Verification**: File exists, header matches exactly, size > 0 KB.  

- [ ] **T007g** [​Manual​] Human labeling of Golden Set  
  - Expert annotators fill `expert_load_score` for ≥ 50 rows in `data/processed/golden_set.csv`.  
  - **Verification**: File present with ≥ 50 non‑empty scores in the range 0‑100.  

- [ ] **T007f** [​P​] Validate & load Golden Set (`code/validation/validate_golden_set.py`)  
  - Checks for `data/processed/golden_set.csv`.  
  - If missing **and** no public dataset with concurrent self‑reports was loaded in **T004**, raise exact halt error:  
    ```
    WAITING_FOR_HUMAN: Golden Set file (data/processed/golden_set.csv) is missing AND no public dataset with concurrent self-reports found. Please complete the manual labeling process described in `docs/golden_set_creation.md` to acquire the Golden Set. The pipeline cannot proceed without external expert labels.
    ```  
  - **Verification**: Running the script on a clean runner produces the error message when the file is absent.  

- [ ] **T011** [​P​] Add configuration & logger (`code/config.py`)  
  - Functions: `load_env()` (reads optional `.env`), `get_logger(name: str)` (standardized formatter).  
  - **Verification**: Importing `code.config` does not raise; `get_logger("test")` returns a logger with name and level INFO.  

---  

## Phase 2 – User Story 1: Cognitive‑Load Estimation (Priority P1)  

- [ ] **T012** [​P​] Contract test for load‑model I/O (`tests/contract/test_load_model.py`)  
  - Validate that `train_load_model.py` reads `data/processed/interactions.csv` and writes `data/processed/load_model.pkl`.  
  - **Verification**: Test fails before implementation, passes after **T014/T015/T015a**.  

- [ ] **T013** [​P​] Integration test for full pipeline (`tests/integration/test_load_model_integration.py`)  
  - End‑to‑end run: data load → golden‑set validation → model training → Pearson‑r check.  
  - **Verification**: Test fails until **T014/T015/T015a/T016/T018** are complete.  

- [ ] **T014** [​US1​] Feature engineering (`code/train_load_model.py`)  
  - Log‑transform latency, count errors, hints, pause duration per session.  
  - Output feature matrix `X.npy` and target vector `y.npy`.  
  - **Verification**: Running the script creates `X.npy` and `y.npy` with matching row counts to `interactions.csv`.  

- [ ] **T015** [​US1​] Train Gradient‑Boosting Regressor (`code/train_load_model.py`)  
  - Use LightGBM (CPU‑only, `tree_method='hist'`).  
  - Load external Golden Set via **T007f** for validation.  
  - Compute Pearson correlation **r** between predictions and `expert_load_score`.  
  - If **r ≥ 0.6** → save model to `data/processed/load_model.pkl` (≤ 500 MB).  
  - If **r < 0.6** → save to `data/processed/load_model_low_confidence.pkl` and log achieved **r**.  
  - **Verification**: After run, appropriate model file exists and a JSON `data/processed/model_metrics.json` records `pearson_r` and a `validation_status` flag.  

- [ ] **T015a** [​US1​] Load‑model validation module (`code/validation/validate_load_model.py`)  
  - Loads the trained model, computes Pearson **r** against the Golden Set, writes metrics to `code/validation/model_metrics.json`.  
  - Ensures the validation artifact lives under `code/validation/` per Constitution VI.  
  - **Verification**: After execution, `code/validation/model_metrics.json` contains `pearson_r`, `validation_status`, and any VIF warnings.  

- [ ] **T016** [​US1​] Collinearity diagnostic (VIF) (`code/train_load_model.py`)  
  - Compute VIF for each predictor; if any VIF > 5, add a warning to `model_metrics.json` and ensure downstream reports phrase relationships descriptively.  
  - **Verification**: `model_metrics.json` contains a `vif_warnings` list when applicable.  

- [ ] **T018** [​US1​] Model‑artifact size check (`code/verify_model_size.py`)  
  - Assert that the final model file (`load_model.pkl` or `_low_confidence.pkl`) is ≤ 500 MB.  
  - Raise error if larger.  
  - **Verification**: Script exits with status 0 on compliant size, non‑zero otherwise.  

---  

## Phase 3 – User Story 2: Explanation‑Complexity Tier Generation (Priority P2)  

- [ ] **T022** [​US2​] Extract instructional units (`code/extract_units.py`)  
  - Pull a sample of instructional texts (e.g., ASSISTments skill descriptions) and write `data/processed/instructional_units.csv`.  
  - **Verification**: CSV contains at least 20 rows with columns `unit_id`, `source_text`.  

- [ ] **T022b** [​US2​] Generate moderate tier (`code/generate_tiers.py`)  
  - Copy source text to `data/explanation_tiers/moderate_tiers.csv` (adds `tier_level='moderate'`).  
  - **Verification**: File exists and each row has `tier_id`, `source_item_id`, `tier_level`, `text_content`.  

- [ ] **T023** [​US2​] Generate simple tier with constraints (`code/generate_tiers.py`)  
  - Apply deterministic simplification loop (max 3 attempts) to achieve:  
    - Flesch‑Kincaid grade ≤ moderate − 5.  
    - Jaccard similarity ≥ 0.85.  
  - Output to `data/explanation_tiers/simple_tiers.csv`.  
  - **Verification**: All rows satisfy both numeric constraints; script raises a clear `ValueError` if not.  

- [ ] **T024** [​US2​] Generate complex tier with constraints (`code/generate_tiers.py`)  
  - Apply deterministic complexity‑enhancement loop (max 3 attempts) to achieve:  
    - Flesch‑Kincaid grade ≥ moderate + 5.  
    - Jaccard similarity ≥ 0.85.  
  - Output to `data/explanation_tiers/complex_tiers.csv`.  
  - **Verification**: Same as **T023** but for the opposite direction.  

- [ ] **T025** [​US2​] Tier validation & metadata (`code/validate_tiers.py`)  
  - Compute readability, Jaccard, and semantic similarity (TF‑IDF cosine) for all three tiers.  
  - Ensure monotonic progression (simple < moderate < complex) with ≥ 5‑point FK gaps and similarity thresholds (Jaccard ≥ 0.85, semantic ≥ 0.90).  
  - Save consolidated metadata `data/explanation_tiers/tier_metadata.json`.  
  - **Verification**: JSON contains per‑tier metrics and a top‑level flag `validation_passed: true`.  

- [ ] **T026** [​US2​] Document tier generation (`docs/research.md`)  
  - Add a “Complexity Tier Generation” subsection describing algorithms, constraints, and validation results.  
  - **Verification**: The subsection appears and references `tier_metadata.json`.  

---  

## Phase 4 – User Story 3: Adaptive vs Static Simulation (Priority P3)  

- [ ] **T040** [​P​] Add retrieval‑latency extraction (`code/simulate_sessions.py`)  
  - For each interaction, compute `retrieval_latency = first_correct_response_timestamp – question_presented_timestamp`.  
  - Store `retrieval_latency` in both static and adaptive result CSVs.  
  - **Verification**: New column `retrieval_latency` exists and contains non‑negative floats.  

- [ ] **T029** [​US3​] Session replay logic (`code/simulate_sessions.py`)  
  - Load ≥ 40 historical sessions from `data/processed/interactions.csv`.  
  - Produce `data/simulation_results/replayed_sessions.json`.  
  - **Verification**: JSON contains exactly the requested number of session objects.  

- [ ] **T030** [​US3​] Static‑condition simulation (`code/simulate_sessions.py`)  
  - For each replayed session, always serve the **moderate** tier.  
  - Record predicted engagement time and potential gain per session.  
  - Output `data/simulation_results/static_simulation.csv`.  
  - **Verification**: CSV includes columns `session_id`, `condition='static'`, `efficiency_score`.  

- [ ] **T032** [​US3​] Hysteresis controller config (`code/hysteresis.py`)  
  - After successful model validation (**T015** with **r ≥ 0.6**), write `data/simulation_results/hysteresis_config.json` containing `baseline_threshold` (e.g., 0.3) and `hysteresis_band='moderate'`.  
  - **Verification**: JSON file exists and schema matches the specification.  

- [ ] **T031a** [​US3​] Hysteresis controller implementation (`code/hysteresis.py`)  
  - Implements the decision‑making logic that selects a complexity tier based on load estimate, baseline threshold, and hysteresis band.  
  - Includes unit tests (`tests/unit/test_hysteresis.py`).  
  - **Verification**: Unit tests pass; `simulate_sessions.py` imports and uses this controller.  

- [ ] **T031** [​US3​] Adaptive‑condition simulation (`code/simulate_sessions.py`)  
  - Use load‑model predictions, apply hysteresis controller, and enforce **min_struggle_count = 2** before downgrading tier (struggle preservation).  
  - Output `data/simulation_results/adaptive_simulation.csv`.  
  - **Verification**: CSV includes `complexity_tier` per interaction and respects the struggle rule (no tier downgrade after a single error).  

- [ ] **T033** [​US3​] Hysteresis sensitivity analysis (`code/hysteresis_sensitivity.py`)  
  - Sweep absolute‑diff thresholds `{0.01, 0.05, 0.1}`; compute `inconsistency_rate` as tier‑switch count / total transitions.  
  - Save `data/simulation_results/hysteresis_sensitivity.csv`.  
  - **Verification**: CSV has three rows with the required columns and numeric values between 0 and 1.  

- [ ] **T034** [​US3​] Learning‑efficiency metric (`code/compute_efficiency.py`)  
  - Formula: `(predicted_engagement_time × gain_factor) / total_time`.  
  - Append `efficiency_score` to both static and adaptive result files.  
  - **Verification**: New column appears and values are numeric > 0.  

- [ ] **T035** [​US3​] Mixed‑effects model fitting (`code/analyze_results.py`)  
  - Fit LMM with fixed effects: `condition`, `estimated_load`, `condition × estimated_load`; random intercept for `session_id`.  
  - Produce `data/simulation_results/mixed_effects_summary.json` containing `cohen_d`, `ci_lower`, `ci_upper`, `p_value`, `correction_applied`.  
  - **Verification**: JSON includes all fields and `p_value` < 0.05 when the simulated effect is present.  

- [ ] **T037a** [​US3​] Multiple‑comparison correction (`code/analyze_results.py`)  
  - Apply Bonferroni (or similar) correction when >1 hypothesis test is performed, record the method in `correction_applied`.  
  - **Verification**: `mixed_effects_summary.json` reflects the applied correction.  

- [ ] **T036** [​US3​] Statistical reporting (`code/report_stats.py`)  
  - Read the LMM summary and generate a human‑readable markdown report `docs/simulation_report.md` with effect size, confidence interval, and correction note.  
  - **Verification**: Report file renders correctly on GitHub (markdown table present).  

- [ ] **T037** [​US3​] Associational framing (`code/report_stats.py`)  
  - Append a disclaimer to `docs/simulation_report.md`: *“All findings are associational; no causal claims are made.”*  
  - **Verification**: Disclaimer string is present verbatim.  

- [ ] **T038** [​US3​] Power‑limitation check (`code/check_power.py`)  
  - If number of sessions **N < 40**, write warning to `docs/simulation_report.md` and skip effect‑size claim.  
  - **Verification**: When N < 40, the warning appears; otherwise, it does not.  

---  

## Phase 5 – Review‑Driven Revisions & Documentation  

- [ ] **T040a** [​Rev​] Implement `code/analyze_results.py` (wrapper for mixed‑effects analysis)  
  - Calls the LMM fitting routine, applies multiple‑comparison correction, writes `mixed_effects_summary.json`.  
  - **Verification**: Script runs without error and produces the expected JSON file.  

- [ ] **T041** [​Rev​] Update `docs/research.md` & `README.md` with limitation statement  
  - Explain why self‑reported ease is excluded and how the Golden Set provides external validation.  
  - **Verification**: Both files contain the exact paragraph: *“Self‑reported ease is not used as a primary metric due to the risk of the ‘illusion of competence’; primary metrics focus on behavioral proxies validated against expert‑labeled load.”*  

- [ ] **T042** [​Rev​] Frame retrieval‑latency findings as associational (`code/report_stats.py`)  
  - Add a subsection “Retrieval Latency (Associational Indicator)” with descriptive statistics per condition.  
  - **Verification**: Subsection appears in `docs/simulation_report.md`.  

- [ ] **T054** [​Rev​] Document “System 2 Preservation” (`docs/research.md`)  
  - Detail the hysteresis controller, `min_struggle_count`, and retrieval‑latency metric as safeguards against premature simplification.  
  - Cite the implementation locations (`code/simulate_sessions.py` lines … and `code/report_stats.py`).  
  - **Verification**: Section titled **System 2 Preservation** exists and references the two code files.  

- [ ] **T056** [​Rev​] Update `README.md` to surface “System 2 Preservation” warning in the project overview.  
  - **Verification**: README contains a bullet: *“System 2 Preservation – adaptive logic includes hysteresis and struggle‑preservation to avoid the illusion of competence.”*  

---  

## Phase 6 – Polish, Performance & End‑to‑End Validation  

- [ ] **T057** [​P​] Refactor `code/utils.py` & add unit tests (`tests/unit/test_utils.py`)  
  - Ensure each utility function is covered by at least one test case.  
  - **Verification**: `pytest -q` reports 100 % pass.  

- [ ] **T058a** [​P​] Resource‑compliance verification (`code/check_resources.py`)  
  - Assert that the process uses ≤ 2 CPU cores, ≤ 7 GB RAM, and total wall‑clock time ≤ 6 h.  
  - Fail the pipeline with a clear error if limits are exceeded.  
  - **Verification**: Script exits with status 0 when within limits, non‑zero otherwise.  

- [ ] **T058** [​P​] Profile & optimise `code/train_load_model.py`  
  - Use `cProfile` to ensure total training time ≤ 30 minutes on the free‑tier runner.  
  - Apply `max_bin` and `num_leaves` tuning for LightGBM to stay within the 6‑hour wall‑clock budget.  
  - **Verification**: Log file `logs/train_load_model_time.log` records elapsed time < 1800 s.  

- [ ] **T039a** [​P​] Pipeline wrapper (`code/run_pipeline.py`)  
  - Orchestrates: data loading → golden‑set validation → load‑model training → tier generation → simulations → analysis.  
  - Measures total wall‑clock time; raises `TimeoutError` if > 6 h, logging the offending stage.  
  - **Verification**: Script exits with status 0 on successful run; on artificial delay (> 6 h) it raises the expected exception.  

- [ ] **T059** [​P​] Create `quickstart.md` with a single runnable command  
  - Command: `python -m code.run_pipeline`.  
  - Include expected output locations.  
  - **Verification**: Running the command on a fresh runner completes without errors and produces all result files.  

---  

### Dependency & Execution Order Summary  

1. **Setup**: T001 → T001a → T001b → T002 → T003 → T004 → T005 → T006 → T011  
2. **Golden‑Set**: T006 → T007g (manual) → T007f → T015a (validation placement)  
3. **Load Model**: T012/T013 (tests) → T014 → T015 → T015a → T016 → T018 → T058a (resource check)  
4. **Tier Generation**: T022 → T022b → T023 → T024 → T025 → T026  
5. **Simulation**: T040 → T029 → T030 → T032 → T031a → T031 → T033 → T034 → T035 → T037a → T036 → T037 → T038  
6. **Review Revisions**: T040a → T041 → T042 → T054 → T056  
7. **Polish**: T057 → T058 → T059 → T039a  

All tasks are unchecked until their implementation is verified; previously completed tasks (e.g., T002, T003, T006, T011) remain marked as completed.  

---  

*End of `tasks.md`.*  