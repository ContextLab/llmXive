# Tasks: llmXive follow‑up: extending “Translation as a Bridging Action”

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contracts, and any existing artifacts.

The list preserves all previously verified (checked) work and re‑opens only the tasks that were rejected or found incomplete.  Sub‑tasks are grouped by research phase and user story.  All unchecked items must be implemented to satisfy the specification, and the overall pipeline should be runnable end‑to‑end with a single command (see the final “Quick‑start validation” task).

---  

## Phase 1 – Project scaffolding  

- [ ] T001 Create project structure under `projects/PROJ-855-llmxive-follow-up-extending-translation/` including `contracts/`, `code/`, `data/`, `tests/`, and `requirements.txt`. **Artifact**: directory tree existence. **Verification**: run `tests/integration/test_scaffolding.py` which checks for required sub‑directories and files.  
- [ ] T001b Generate `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml` from `data‑model.md`. **Artifact**: the two schema files. **Verification**: `jsonschema` validation test `tests/contract/test_schema_valid.py`.  
- [ ] T002 Initialise a Python 3.10 environment and pin dependencies in `code/requirements.txt`. **Artifact**: `code/requirements.txt`. **Verification**: `pip install -r code/requirements.txt` succeeds in CI.  
- [ ] T003 Configure linting (ruff) and formatting tools. **Artifact**: `.ruff.toml` (or `pyproject.toml` with ruff config). **Verification**: `ruff check .` returns no errors in CI.  

## Phase 2 – Foundational utilities  

- [ ] T005b Create `code/config.yaml` with required numeric thresholds (`tipping_angle: 15.0`, `slippage_distance: 0.02`) and placeholders for sensitivity‑analysis sweep parameters. **Artifact**: `code/config.yaml`. **Verification**: `tests/unit/test_config_load.py` ensures file parses and contains required keys.  
- [ ] T005a Implement `code/utils/physics_metrics.py` to compute tipping angle and slippage distance, **loading thresholds from `config.yaml`**. **Artifact**: `code/utils/physics_metrics.py`. **Verification**: `tests/unit/test_physics_metrics.py` validates calculations against known values.  
- [ ] T004 Implement `code/utils/data_utils.py` for schema validation and checksum handling. **Artifact**: `code/utils/data_utils.py`. **Verification**: `tests/unit/test_data_utils.py`.  
- [ ] T006 Create the `data/` directory hierarchy (`raw/`, `processed/`, `sweep/`) and initialise an empty `data/checksums.json`. **Artifact**: `data/checksums.json`. **Verification**: file exists and is a valid empty JSON object.  
- [ ] T007 Implement `tests/unit/test_labeling.py` to validate the physics‑metric calculations. **Artifact**: test file. **Verification**: pytest passes.  
- [ ] T008 Implement `tests/contract/test_schemas.py` to validate outputs against the JSON schemas. **Artifact**: test file. **Verification**: pytest passes.  

## Phase 3 – User Story 1: Synthetic data generation & labeling (P1)

- [ ] T009 Contract test for dataset schema (`tests/contract/test_dataset_schema.py`). **Artifact**: test file. **Verification**: passes after data generation.  
- [ ] T010 Unit test for stability‑labeling logic (`tests/unit/test_labeling_logic.py`). **Artifact**: test file. **Verification**: passes.  

- [ ] T011 Implement `code/generate_data.py` with a deterministic PyBullet simulation loop that records **only** translation vectors and initial object bounds. **Artifact**: `code/generate_data.py`. **Verification**: script runs without CUDA imports and creates raw dataset.  
- [ ] T011b Add logic to generate a unique `geometry_id` for each episode. **Artifact**: part of `generate_data.py`. **Verification**: `tests/unit/test_geometry_id.py` checks uniqueness.  
- [ ] T012 Ensure that rotation, joint‑torque, and force‑sensor fields are never written. **Artifact**: part of `generate_data.py`. **Verification**: `tests/contract/test_forbidden_columns.py` validates absence of forbidden columns.  
- [ ] T014 Add robust error handling: on any simulation exception, log the failure, discard the incomplete episode, and generate a replacement until the dataset reaches **≥ 5 000** valid rows. **Artifact**: enhanced `generate_data.py`. **Verification**: `tests/integration/test_generation_count.py` asserts row count ≥ 5 000 after run.  
- [ ] T016 Generate the raw dataset `data/raw/synthetic_episodes.parquet` (≥ 5 000 rows). **Artifact**: `data/raw/synthetic_episodes.parquet`. **Verification**: row count check + schema validation.  
- [ ] T016b Verify that the raw Parquet file exists, is non‑empty, and conforms to `contracts/dataset.schema.yaml`. **Artifact**: verification step (part of CI).  
- [ ] T016c Perform a geometry‑disjoint split of the raw data into `data/processed/train.parquet` and `data/processed/test.parquet` (80/20 split, no overlapping `geometry_id`s) and validate both files against the schema. **Artifacts**: `data/processed/train.parquet`, `data/processed/test.parquet`. **Verification**: `tests/contract/test_split_integrity.py`.  
- [ ] T018 Replace the previous sweep task with **degree‑based** sensitivity analysis (see Phase 5). The old `relabel_and_split` remains for threshold sweeps only. **Artifact**: function `relabel_and_split` in `generate_data.py`. **Verification**: unit test `tests/unit/test_relabel_and_split.py`.  

## Phase 4 – User Story 2: Lightweight sequence model training (P2)

- [ ] T019 Unit test confirming the Transformer architecture stays below **10 000 000** parameters. **Artifact**: test file. **Verification**: `tests/unit/test_parameter_count.py`.  
- [ ] T020 Integration test that the training loop runs on a CPU‑only runner without CUDA imports. **Artifact**: test file. **Verification**: passes in CI.  

- [ ] T021 Implement `code/models/transformer.py` – a 4‑layer PyramidTNT‑Ti‑style encoder respecting the parameter cap. **Artifact**: `code/models/transformer.py`. **Verification**: import test `tests/unit/test_transformer_import.py`.  
- [ ] T022 Implement `code/train_model.py` to load `data/processed/train.parquet`, train the Transformer with binary cross‑entropy loss, and enforce CPU‑only execution. **Artifact**: `code/train_model.py`. **Verification**: script runs and produces model file.  
- [ ] T023 Add runtime monitoring (using `psutil`) that logs peak RAM (`[RAM-PEAK-MB]: …`) and aborts if RAM > 7 GB or wall‑clock > 6 h. **Artifact**: logging in `train_model.py`. **Verification**: `tests/unit/test_runtime_monitor.py`.  
- [ ] T024 Save the trained weights to `data/processed/trained_model.pt`. **Artifact**: `data/processed/trained_model.pt`. **Verification**: file existence check after training.  
- [ ] T025 After training, write `data/processed/model_summary.txt` containing the exact parameter count and a brief architecture description. **Artifact**: `data/processed/model_summary.txt`. **Verification**: `tests/unit/test_model_summary.py` asserts count < 10 M.  

- [ ] T025b Implement `code/train_baseline.py` – a lightweight MLP (or scikit‑learn Logistic Regression) using only `initial_bounds` as features; save to `data/processed/geometry_baseline.pt`. **Artifact**: `data/processed/geometry_baseline.pt`. **Verification**: script runs and file exists.  
- [ ] T025c Implement `code/train_shuffled_control.py` – shuffle each episode’s translation sequence (seed = 42) to destroy temporal structure, train a model of identical architecture, and save to `data/processed/random_baseline.pt`. **Artifact**: `data/processed/random_baseline.pt`. **Verification**: script runs and file exists.  
- [ ] T042 Implement and persist a **Class Prior Baseline** (`data/processed/class_prior_baseline.pt`) that always predicts the majority class. **Artifact**: `data/processed/class_prior_baseline.pt`. **Verification**: `tests/unit/test_class_prior.py`.  

- [ ] T043 Generate `data/checksums.json` containing SHA‑256 hashes for all newly created data artifacts (`synthetic_episodes.parquet`, `train.parquet`, `test.parquet`, model files, baselines). **Artifact**: `data/checksums.json`. **Verification**: `tests/unit/test_checksums.py` confirms all entries present and correct.  

- [ ] T044 Extract the total parameter count from `data/processed/model_summary.txt` and store it for later use. **Artifact**: helper script (`code/extract_param_count.py`). **Verification**: unit test `tests/unit/test_extract_param_count.py`.  

- [ ] T045 Insert the extracted `parameter_count` into `data/processed/metrics_report.json` (field `parameter_count`). **Artifact**: updated `metrics_report.json`. **Verification**: schema test `tests/contract/test_report_schema.py`.  

## Phase 5 – User Story 3: Statistical validation & baseline comparison (P3)

- [ ] T026 Unit test for McNemar’s test implementation (`tests/unit/test_mcnemar.py`). **Artifact**: test file. **Verification**: passes.  
- [ ] T027 Contract test for `metrics_report.json` (`tests/contract/test_metrics_report.py`). **Artifact**: test file. **Verification**: passes.  

- [ ] T028 Implement `code/evaluate.py` to load the three models (`trained_model.pt`, `geometry_baseline.pt`, `random_baseline.pt`) and produce predictions on `data/processed/test.parquet`. **Artifact**: `code/evaluate.py`. **Verification**: script runs without errors.  
- [ ] T029 Save predictions as `data/processed/predictions_main.json`, `predictions_geometry.json`, and `predictions_random.json` conforming to `contracts/model_output.schema.yaml`. **Artifacts**: three JSON files. **Verification**: `tests/contract/test_model_output.py`.  
- [ ] T030 Compute McNemar’s test (model vs geometry) and log the p‑value to stdout and to `data/processed/metrics_report.json`. **Artifact**: updated `metrics_report.json`. **Verification**: `tests/unit/test_mcnemar_geometry.py`.  
- [ ] T031 Compute McNemar’s test (model vs random) and record the p‑value similarly. **Verification**: `tests/unit/test_mcnemar_random.py`.  
- [ ] T032 Calculate accuracy for all three models; enforce **accuracy improvement ≥ 0.02** over each baseline, aborting with a clear error if the condition fails. **Verification**: part of `evaluate.py` with exit code non‑zero on failure.  

- [ ] T033a Load all `data/processed/sweep_*.parquet` files produced by T018 (threshold sweep). **Verification**: existence check.  
- [ ] T033b For each sweep file, re‑evaluate the trained main model (no retraining) and record accuracy. **Verification**: `tests/unit/test_sweep_accuracy.py`.  
- [ ] T033c Aggregate the sweep accuracies, compute the standard deviation, and append `sensitivity_variance` to `metrics_report.json`. **Verification**: part of `sensitivity.py`.  

- [ ] T051 Implement the **degree‑based** sensitivity analysis: inject Gaussian noise (σ ∈ {0.0, 0.25, 0.5, 0.75, 1.0}°) into each translation vector, re‑evaluate the main model, and store per‑σ accuracies in `data/sweep/variance_report.json`. **Artifact**: `data/sweep/variance_report.json`. **Verification**: `tests/unit/test_sensitivity_variance.py`.  

- [ ] T046 Monitor baseline accuracies; if any baseline accuracy < 55 %, set `baseline_convergence_flag: true` in `metrics_report.json`. **Artifact**: updated `metrics_report.json`. **Verification**: unit test `tests/unit/test_baseline_convergence.py`.  

- [ ] T034a Generate the final `data/processed/metrics_report.json` containing:
  - `model_accuracy`, `baseline_accuracy`, `control_accuracy`
  - `accuracy_improvement`
  - `mcnemar_p_value` (both comparisons)
  - `confusion_matrix` (TP, TN, FP, FN)
  - `sensitivity_variance`
  - `associational_framing: true`
  - `runtime_seconds` and `peak_ram_gb` from T023
  - `parameter_count` from T045
  - `baseline_convergence_flag` from T046
  - `ambiguous_subset_flag` from T036a
  - `reproducibility_flag` from T054
  **Artifact**: `data/processed/metrics_report.json`. **Verification**: `tests/contract/test_report_schema.py`.  

- [ ] T035a Verify that the test set contains no `geometry_id` present in the training set; raise an error if any overlap is detected. **Verification**: part of `evaluate.py` with explicit check.  

- [ ] T036a Detect episodes where translation sequences are identical (within 1e‑5) but have opposite stability labels; compute a separate confusion matrix for this subset and, if its accuracy < 0.5, add an `ambiguous_subset_flag: true` field to `metrics_report.json`. **Verification**: `tests/unit/test_ambiguous_subset.py`.  

- [ ] T047 Run the Class Prior Baseline on the test set and store its predictions in `data/processed/predictions_class_prior.json` (conforming to `model_output.schema.yaml`). **Artifact**: `data/processed/predictions_class_prior.json`. **Verification**: schema test `tests/contract/test_model_output.py`.  

- [ ] T048 Verify that the `parameter_count` recorded in `model_summary.txt` matches the `parameter_count` field in `metrics_report.json`. **Artifact**: validation step in `code/validate_report.py`. **Verification**: unit test `tests/unit/test_parameter_report_consistency.py`.  

- [ ] T049 Execute a full pipeline integrity check: ensure all expected artifacts exist, their checksums match `data/checksums.json`, and that re‑running `code/evaluate.py` yields an identical `metrics_report.json`. **Artifact**: `pipeline_integrity_check.log`. **Verification**: integration test `tests/integration/test_pipeline_integrity.py`.  

- [ ] T050 Produce a concise markdown summary `docs/report_summary.md` that links to `metrics_report.json`, includes key numbers, and references the associative‑framing statement. **Artifact**: `docs/report_summary.md`. **Verification**: CI grep for required sections.  

- [ ] T053 Audit independence: static analysis ensures `generate_data.py` does **not** import or read `config.yaml` during trajectory generation. **Artifact**: audit script `tests/unit/test_independence.py`. **Verification**: passes.  

- [ ] T054 Re‑run `code/evaluate.py` after the pipeline completes and assert the newly generated `metrics_report.json` is byte‑identical to the previously saved one; write a `reproducibility_flag` into the report. **Verification**: `tests/integration/test_reproducibility.py`.  

- [ ] T055 Wrap the entire pipeline in a timer (`code/quickstart.sh`) and fail if wall‑clock exceeds 6 h; write runtime to `pipeline_runtime.txt`. **Artifact**: `pipeline_runtime.txt`. **Verification**: CI step checks file and exit code.  

## Phase 6 – Cross‑cutting verification & hand‑off  

- [ ] T037 Update `README.md` and `docs/report.md` with a concise description of the pipeline, artifact locations, and a **section “Associative Framing”** that explicitly states results are presented associatively (covers FR‑011). **Artifact**: `README.md`, `docs/report.md`. **Verification**: grep for “associative framing” in CI.  
- [ ] T038 Code cleanup and refactoring across `code/` to remove any stray `torch.cuda` imports. **Verification**: `grep -R "torch.cuda" code/` returns no matches in CI.  
- [ ] T039 Performance optimisation to keep total wall‑clock < 6 h (e.g., batch‑size tuning, early‑stopping). **Verification**: ensured by T055 runtime check.  
- [ ] T040 Add edge‑case unit tests for simulation tunnelling and ambiguous‑signal detection (`tests/unit/test_edge_cases.py`). **Verification**: pytest passes.  
- [ ] T041a **Quick‑start validation** – Add script `code/quickstart.sh` that executes the full pipeline in order:
  1. `python code/generate_data.py`
  2. `python code/train_model.py`
  3. `python code/train_baseline.py`
  4. `python code/train_shuffled_control.py`
  5. `python code/train_class_prior.py` (new script for T042)
  6. `python code/evaluate.py`
  7. `python code/sensitivity.py` (optional)
  The script must exit with code 0, print `PIPELINE‑SUCCESS`, and write `pipeline_runtime.txt`. **Verification**: CI runs script and checks exit code and output.  

- [ ] T052 Verify that labeling logic in `generate_data.py` reads thresholds from `config.yaml` and applies them correctly. **Artifact**: part of `generate_data.py`. **Verification**: `tests/unit/test_labeling_respects_config.py`.  

- [ ] T056 Contract test that generated Parquet files contain no forbidden columns as defined in `contracts/dataset.schema.yaml`. **Artifact**: test file. **Verification**: passes after data generation.  

- [ ] T057 Ensure that `metrics_report.json` includes `parameter_count` matching the value in `model_summary.txt`. **Verification**: `tests/unit/test_parameter_report_consistency.py`.  

- [ ] T058 Verify that `data/checksums.json` entries match the actual SHA‑256 hashes of all data artifacts. **Verification**: `tests/unit/test_checksum_validation.py`.  

- [ ] T059 Implement baseline convergence monitoring in `code/evaluate.py`, flagging if any baseline accuracy < 55 % and persisting `baseline_convergence_flag` in `metrics_report.json`. **Verification**: unit test `tests/unit/test_baseline_convergence.py` ensures flag is set correctly.  

- [ ] T060 Ensure final report and README explicitly state associative framing per FR‑011. Update `docs/report.md` and `README.md` with a section "Associative Framing". **Verification**: grep for “associative framing” in CI.  

---  

### Dependencies & execution order (updated)

| Task | Depends on |
|------|------------|
| T005b | – |
| T005a | T005b |
| T014 | T005b |
| T016‑T016c | T014 |
| T018 | T016c |
| T021 | – |
| T022 | T021, T016c |
| T023 | T022 |
| T024 | T023 |
| T025 | T024 |
| T025b | T016c |
| T025c | T016c |
| T042 | T016c |
| T043 | T016c, T024, T025b, T025c, T042 |
| T044 | T025 |
| T045 | T044 |
| T046 | T028 |
| T047 | T028 |
| T048 | T045, T057 |
| T049 | T043, T028, T054 |
| T050 | T037 |
| T051 | T016c |
| T052 | T011 |
| T053 | T011 |
| T054 | T034a |
| T055 | T041a |
| T056 | T016c |
| T057 | T044, T025 |
| T058 | T043 |
| T059 | T028 |
| T060 | T037 |

Running `code/quickstart.sh` will respect this order automatically.

---  

### Verification checklist (all tasks must pass)

- **Config file** (`code/config.yaml`) present, parsable, and used by labeling.  
- **Raw dataset** (`data/raw/synthetic_episodes.parquet`) ≥ 5 000 rows, no forbidden columns, checksum recorded.  
- **Train/Test splits** geometry‑disjoint, validated against schema.  
- **Transformer model** saved, parameter count < 10 M, `model_summary.txt` present.  
- **Baseline models** (`geometry_baseline.pt`, `random_baseline.pt`, `class_prior_baseline.pt`) saved.  
- **Predictions** and **metrics_report.json** conform to contracts, include all required fields and flags.  
- **Sensitivity sweep** files generated, variance reported.  
- **Quick‑start script** runs end‑to‑end, prints `PIPELINE‑SUCCESS`, respects runtime limit.  
- **All contract and unit tests** pass.  

---  

*All unchecked tasks must be completed before the next analysis round.  Once every artifact exists and all contract tests pass, the verifier should accept the project as “research_complete”.*  