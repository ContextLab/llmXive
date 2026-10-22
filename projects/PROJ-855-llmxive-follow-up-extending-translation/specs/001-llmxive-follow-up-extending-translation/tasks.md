# Tasks: llmXive follow‑up – extending “Translation as a Bridging Action”

**Inputs**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, all JSON‑schema contracts, and any existing artifacts.

The list below consolidates the required work into 19 substantive research tasks, grouped by research phase.  Each task follows the canonical checklist format, names the exact artifact it produces, and specifies an observable verification step.  All previously verified (checked) work is retained; unchecked tasks are those that still need implementation or correction.

---  

## Phase 1 – Project scaffolding & configuration  

- [ ] T001 Create `code/config.yaml` containing the deterministic random seed, labeling thresholds (`tipping_angle: 15.0`, `slippage_distance: 0.02`), and sensitivity‑analysis noise levels (σ in **degrees**).  
  - **Artifact**: `code/config.yaml`  
  - **Verification**: `tests/unit/test_config_load.py` parses the file and asserts the required keys exist with correct types.  

- [ ] T002 Implement `code/generate_data.py` to run a deterministic PyBullet simulation loop that records **only** `translation_sequence` and `initial_bounds` for each episode (no rotation, torque, or force columns).   <!-- FAILED-IN-EXECUTION: code/generate_data.py exit=1 -->
  - **Artifact**: `code/generate_data.py`  
  - **Verification**: `pytest tests/unit/test_generate_data.py` checks that the script runs without importing `torch.cuda` and writes a Parquet file at `data/raw/synthetic_episodes.parquet`.  

- [ ] T003 Add robust error handling to `generate_data.py`: on any simulation exception, log the failure, discard the incomplete episode, and generate a replacement until the total number of **valid** episodes reaches **≥ 5 000**.  
  - **Artifact**: Updated `code/generate_data.py` (exception‑handling block).  
  - **Verification**: `tests/integration/test_generation_count.py` asserts the final row count ≥ 5 000.  

---  

## Phase 2 – Post‑generation labeling & split (addresses FR‑013 & rejected tasks T014, T016‑T016c, T018)  

- [ ] T004 Implement `code/relabel_and_split.py` that **loads** `data/raw/synthetic_episodes.parquet`, **reads** thresholds from `config.yaml`, computes `stability_label` using `tipping_angle` and `slippage_distance`, **drops** all forbidden columns, and writes the processed dataset to `data/processed/full_processed.parquet`.  
  - **Artifact**: `code/relabel_and_split.py`  
  - **Verification**: `tests/unit/test_labeling_logic.py` validates that the label matches the threshold logic and that forbidden columns are absent.  

- [ ] T005 Perform a **geometry‑disjoint** split of `full_processed.parquet` into `data/processed/train.parquet` (80 %) and `data/processed/test.parquet` (20 %) ensuring no overlapping `geometry_id`s.  
  - **Artifact**: `data/processed/train.parquet`, `data/processed/test.parquet`  
  - **Verification**: `tests/contract/test_split_integrity.py` checks that the intersection of `geometry_id`s is empty and that both files conform to `dataset.schema.yaml`.  

- [ ] T006 Update `data/checksums.json` with SHA‑256 hashes for `synthetic_episodes.parquet`, `full_processed.parquet`, `train.parquet`, and `test.parquet`.  
  - **Artifact**: `data/checksums.json`  
  - **Verification**: `tests/unit/test_checksums.py` recomputes hashes and asserts they match the recorded values.  

---  

## Phase 3 – Main model implementation & training (addresses T024, T025)  

- [ ] T007 Implement `code/models/transformer.py` – a 4‑layer PyramidTNT‑Ti‑style encoder whose total parameter count is **strictly < 10 000 000**.  
  - **Artifact**: `code/models/transformer.py`  
  - **Verification**: `tests/unit/test_parameter_count.py` loads the model and asserts `parameter_count < 10_000_000`.  

- [ ] T008 Implement `code/train_model.py` to load `train.parquet`, train the Transformer with binary cross‑entropy loss on CPU‑only, enforce a wall‑clock limit of 6 h and peak RAM ≤ 7 GB (using `psutil`), and save the weights to `data/processed/trained_model.pt`.  
  - **Artifact**: `data/processed/trained_model.pt`  
  - **Verification**: `tests/integration/test_training.py` runs the script and checks that the file exists and that the log contains `RAM‑PEAK‑GB` ≤ 7 and `TRAINING‑TIME‑SEC` ≤ 21600.  

- [ ] T009 After training, write `data/processed/model_summary.txt` containing the exact parameter count and a brief architecture description.  
  - **Artifact**: `data/processed/model_summary.txt`  
  - **Verification**: `tests/unit/test_model_summary.py` parses the file and confirms the count matches the value from `transformer.py` and is < 10 M.  

---  

## Phase 4 – Baseline & control models (addresses rejected baseline task)  

- [ ] T010 Implement `code/train_baseline.py` – a lightweight MLP that consumes only `initial_bounds` to predict `stability_label`; train on `train.parquet` and save to `data/processed/geometry_baseline.pt`.  
  - **Artifact**: `data/processed/geometry_baseline.pt`  
  - **Verification**: `tests/integration/test_geometry_baseline.py` runs the script and checks the file exists.  

- [ ] T011 Implement `code/train_shuffled_control.py` – shuffle each episode’s `translation_sequence` (seed = 42) to destroy temporal structure, train a Transformer of identical architecture as the main model, and save to `data/processed/random_baseline.pt`.  
  - **Artifact**: `data/processed/random_baseline.pt`  
  - **Verification**: `tests/integration/test_random_baseline.py` runs the script and validates existence.  

- [ ] T012 Implement `code/train_class_prior.py` – compute the majority class in the training set, create a dummy model that always predicts that class, and save to `data/processed/class_prior_baseline.pt`.  
  - **Artifact**: `data/processed/class_prior_baseline.pt`  
  - **Verification**: `tests/unit/test_class_prior.py` loads the file and checks that all predictions equal the majority label.  

---  

## Phase 5 – Evaluation & statistical validation (covers FR‑008, FR‑011, SC‑003, SC‑004, SC‑008, SC‑010)  

- [ ] T013 Implement `code/evaluate.py` to load the three trained models (`trained_model.pt`, `geometry_baseline.pt`, `random_baseline.pt`) **and** the class‑prior baseline (`class_prior_baseline.pt`), generate predictions on `test.parquet`, compute **accuracy**, **AUC‑ROC**, and a **confusion matrix** for each, and write the three JSON prediction files (`model_output_main.json`, `model_output_geometry.json`, `model_output_random.json`) conforming to `model_output.schema.yaml`.  
  - **Artifacts**: `data/processed/model_output_main.json`, `data/processed/model_output_geometry.json`, `data/processed/model_output_random.json`  
  - **Verification**: `tests/contract/test_model_output.py` validates each JSON against the schema.  

- [ ] T014 Within `evaluate.py`, perform **McNemar’s test** for (a) main vs. geometry baseline and (b) main vs. random baseline; record both p‑values in `data/processed/metrics_report.json`.  
  - **Artifact**: `data/processed/metrics_report.json` (partial, updated)  
  - **Verification**: `tests/unit/test_mcnemar_geometry.py` and `tests/unit/test_mcnemar_random.py` check that p‑values are computed and stored.  

- [ ] T015 Enforce the **accuracy‑improvement rule**: main model must exceed each baseline by **≥ 0.02**. If not, `evaluate.py` aborts with a clear error message and a non‑zero exit code.  
  - **Verification**: `tests/unit/test_accuracy_improvement.py` runs the script on a deliberately low‑performing model and expects failure.  

- [ ] T016 Detect the **ambiguous‑trajectory subset** (identical `translation_sequence` within tolerance 1e‑5 but opposite `stability_label`). Compute a separate confusion matrix for this subset; if its accuracy < 0.5, add `"ambiguous_subset_flag": true` to `metrics_report.json`.  
  - **Verification**: `tests/unit/test_ambiguous_subset.py` creates a synthetic ambiguous set and checks the flag.  

- [ ] T017 If any baseline accuracy is **< 55 %**, set `"baseline_convergence_flag": true` in `metrics_report.json`.  
  - **Verification**: `tests/unit/test_baseline_convergence.py` validates flag insertion.  

---  

## Phase 6 – Sensitivity analysis (addresses reviewer comment on unit mismatch)  

- **Note**: FR‑009 originally specified σ in degrees; the reviewer highlighted a unit inconsistency.  The following task implements the corrected, **degree‑based** noise injection.  

- [ ] T018 Implement `code/sensitivity.py` that iterates over σ ∈ {0.0°, 0.25°, 0.5°, 0.75°, 1.0°}. For each σ, convert the angle to radians, treat it as a small rotation about a random axis, apply the rotation to each translation vector (preserving magnitude), re‑evaluate the **trained main model** on the unchanged `test.parquet` (no retraining), record the per‑σ accuracy, compute the **standard deviation** across the five accuracies, and write `data/sweep/variance_report.json`.  
  - **Artifact**: `data/sweep/variance_report.json`  
  - **Verification**: `tests/unit/test_sensitivity_variance.py` checks that the file contains five entries and that the computed variance matches a manual calculation.  

- [ ] T019 Append the computed `sensitivity_variance` value to `metrics_report.json` and ensure the schema (`metrics_report.schema.yaml`) validates it.  
  - **Verification**: `tests/contract/test_metrics_report.py` passes after the update.  

---  

## Phase 7 – Independence audit (addresses FR‑013 & reviewer concern)  

- [ ] T020 Add a static‑analysis test `tests/unit/test_independence.py` that parses **all** data‑generation related scripts (`generate_data.py` and any script that writes raw episodes) and asserts they **do not import** `config.yaml` or any labeling thresholds. Labeling logic (`relabel_and_split.py`) is allowed to read thresholds.  
  - **Verification**: test fails if prohibited imports are detected in any generation script.  

---  

## Phase 8 – End‑to‑end pipeline & reproducibility  

- [ ] T021 Create `code/quickstart.sh` that executes the full pipeline in the exact order:  
  1. `python code/generate_data.py`  
  2. `python code/relabel_and_split.py`  
  3. `python code/train_model.py`  
  4. `python code/train_baseline.py`  
  5. `python code/train_shuffled_control.py`  
  6. `python code/train_class_prior.py`  
  7. `python code/evaluate.py`  
  8. `python code/sensitivity.py`  
  The script must exit with code 0, print `PIPELINE‑SUCCESS`, and write total wall‑clock time to `pipeline_runtime.txt`.  
  - **Artifact**: `code/quickstart.sh`, `pipeline_runtime.txt`  
  - **Verification**: CI runs the script and asserts exit code 0, presence of the success message, and that `pipeline_runtime.txt` contains a numeric value ≤ 21600.  

- [ ] T022 Add a reproducibility check: after a full run, re‑execute `code/evaluate.py` and assert that the newly generated `metrics_report.json` is **byte‑identical** to the previously saved one; if so, insert `"reproducibility_flag": true` into the report.  
  - **Verification**: `tests/integration/test_reproducibility.py` performs the double‑run and checks the flag.  

---  

## Phase 9 – Compute‑resource reporting  

- [ ] T025 Collect compute‑resource metrics: parse the training and evaluation logs generated by T008 and T013 to extract total wall‑clock time (`runtime_seconds`) and peak RAM usage (`peak_ram_gb`), then write/merge these fields into `data/processed/metrics_report.json`.  
  - **Artifact**: Updated `data/processed/metrics_report.json` containing `runtime_seconds` and `peak_ram_gb`.  
  - **Verification**: `tests/unit/test_compute_metrics.json` validates that the two fields exist, are numeric, and fall within the SC‑002 limits.  

---  

## Phase 10 – Documentation & final integrity checks  

- [ ] T023 Update `README.md` and `docs/report.md` with a dedicated **Associative Framing** section that explicitly states all results are presented associatively (per FR‑011). Include links to `metrics_report.json` and `report_summary.md`.  
  - **Verification**: CI greps for the phrase “Associative Framing” in both files.  

- [ ] T024 Run the full CI suite (`pytest -q`) to ensure **all** contract, unit, and integration tests pass, that `data/checksums.json` matches the actual artifact hashes, and that the `reproducibility_flag` is set.  
  - **Verification**: CI job succeeds; any failure aborts the pipeline.  

---  

### Dependency & execution order (summary)

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T003, T001 |
| T005 | T004 |
| T006 | T005 |
| T007 | – |
| T008 | T007, T005 |
| T009 | T008 |
| T010 | T005 |
| T011 | T005 |
| T012 | T005 |
| T013 | T008, T010, T011, T012 |
| T014 | T013 |
| T015 | T013 |
| T016 | T013 |
| T017 | T013 |
| T018 | T008, T005 |
| T019 | T018 |
| T020 | T002 |
| T021 | T004‑T019 (all prior steps must succeed) |
| T022 | T021 |
| T025 | T008, T013 |
| T023 | – |
| T024 | All previous tasks (full suite) |

Running `code/quickstart.sh` will automatically respect this order.

---  

**All tasks must be completed and all verification steps must pass before the verifier can accept the project as `research_complete`.**  