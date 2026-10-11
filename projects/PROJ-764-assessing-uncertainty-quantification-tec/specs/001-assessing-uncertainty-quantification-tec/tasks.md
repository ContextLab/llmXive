# Tasks: Assessing Uncertainty Quantification Techniques for Machine‑Predicted Material Properties

**Input**: `spec.md`, `plan.md`, `data-model.md`, and all contract schemas in `specs/001-assessing-uncertainty-quantification-tec/contracts/`.

**Goal**: Deliver a reproducible end‑to‑end pipeline that  

1. downloads the real OQMD subset,  
2. preprocesses it (clean, material‑ID‑stratified split, PCA, exclusion reporting),  
3. trains a 2‑layer baseline NN and three lightweight UQ methods (Deep Ensemble, MC‑Dropout, Sparse GP),  
4. runs inference for all methods,  
5. evaluates calibration (ECE, interval scores, sharpness, aleatoric/epistemic decomposition, seed robustness),  
6. performs the downstream screening case study, and  
7. produces all required artifacts conforming to the SSoT schemas.

---

## Phase 1: Data acquisition & preprocessing

- [ ] T001a [FR-001] [MaterialSample] **Download OQMD subset**  
  *Implementation file*: `code/data/download.py`  
  *Outputs*:  
  - `data/raw/oqmd_subset.parquet` – raw dataset fetched from the verified Hugging Face URL (`https://huggingface.co/datasets/OQMD/OQMD-Subset`).  
  - `data/checksums.json` – SHA‑256 checksum of the raw file; script must recompute and raise on mismatch.  
  *Verification*: pytest checks checksum integrity.

- [ ] T001b [FR-001] [MaterialSample] **Compute structural descriptors**  
  *Implementation file*: `code/data/compute_descriptors.py` (uses `pymatgen`).  
  *Outputs*: adds `atomic_radius` and `packing_fraction` columns to the raw dataframe.  
  *Verification*: unit test validates that both columns exist and contain numeric values for all rows with available CIFs.

- [ ] T001c [FR-001] [FR-010] [SC-005] [MaterialSample] **Validate dataset & generate exclusion report**  
  *Implementation file*: `code/data/validation.py`  
  *Outputs*: `data/validation_report.json` conforming to `validation_report.schema.yaml` (fields: `excluded_count`, `missing_columns`, `total_raw_rows`, `remaining_rows`).  
  *Verification*: schema validation test; rows with missing critical features are excluded from subsequent splits.

- [ ] T001d [FR-001] [FR-002] [MaterialSample] **Material‑ID stratified split (80/10/10)**  
  *Implementation file*: `code/data/preprocess.py`  
  *Outputs*: `data/processed/raw_train.csv`, `data/processed/raw_val.csv`, `data/processed/raw_test.csv` – stratified by `formation_energy` quantiles, `seed=42`, no `material_id` leakage across splits.  
  *Verification*: pytest ensures disjoint `material_id` sets and correct proportions.

- [ ] T001e [FR-005] [MaterialSample] **Fit PCA on training features & export transformed matrices**  
  *Implementation file*: `code/data/pca.py`  
  *Outputs*: `data/processed/pca_transformer.pkl` (≥ 90 % cumulative variance) and PCA‑transformed CSVs `data/processed/features_train_20pca.csv`, `features_val_20pca.csv`, `features_test_20pca.csv`.  
  *Verification*: test asserts explained variance ≥ 0.90 and that transformed files are non‑empty.

---

## Phase 2: Model training

- [ ] T002a [FR-002] **Train baseline feed‑forward NN (≤10 k parameters)**  
  *Implementation file*: `code/models/baseline_nn.py`  
  *Outputs*: `results/models/baseline_nn_arch.pt` – saved architecture; runtime check ensures `≤10 000` parameters and exactly two hidden layers.  
  *Verification*: unit test counts parameters and loads checkpoint on CPU.

- [ ] T002b [FR-003] **Train Deep Ensemble (5 independent seeds 42‑46)**  
  *Implementation file*: `code/models/deep_ensemble.py`  
  *Outputs*: `results/models/ensemble/ensemble_seed_42.pt` … `ensemble_seed_46.pt`.  
  *Verification*: each checkpoint loads; training logs saved.

- [ ] T002c [FR-004] **Train MC‑Dropout models (p=0.2, seeds 42‑44)**  
  *Implementation file*: `code/models/mc_dropout.py`  
  *Outputs*: `results/models/mc_dropout/mc_dropout_seed_42.pt`, `…_43.pt`, `…_44.pt`.  
  *Verification*: checkpoints load; dropout enabled during inference.

- [ ] T002d [FR-005] **Train Sparse Gaussian Process (500 inducing points, fallback to 200)**  
  *Implementation file*: `code/models/sparse_gp.py` (GPyTorch).  
  *Outputs*: `results/models/sparse_gp_model.pt` (records inducing point count used).  
  *Verification*: model loads, reports number of inducing points; warning emitted on fallback.

---

## Phase 3: Unified inference & prediction CSVs

- [ ] T003a [FR-003] [FR-008] **Ensemble inference & uncertainty decomposition**  
  *Implementation file*: `code/models/inference_ensemble.py`  
  *Outputs*: `results/predictions/uq_predictions_ensemble.csv` conforming to `prediction_output.schema.yaml` (includes `aleatoric_variance`, `epistemic_variance`, `uncertainty_type`).  
  *Verification*: schema validator checks variance decomposition consistency.

- [ ] T003b [FR-004] [FR-008] **MC‑Dropout inference (30 stochastic passes)**  
  *Implementation file*: `code/models/inference_mc_dropout.py`  
  *Outputs*: `results/predictions/uq_predictions_mc_dropout.csv` (SSoT schema).  
  *Verification*: same as above.

- [ ] T003c [FR-005] [FR-008] **Sparse GP inference (with reconstruction variance)**  
  *Implementation file*: `code/models/inference_sparse_gp.py`  
  *Outputs*: `results/predictions/uq_predictions_sparse_gp.csv` (includes optional `reconstruction_variance`).  
  *Verification*: schema validation; reconstruction variance column present when applicable.

---

## Phase 4: Calibration metric implementation & evaluation

- [ ] T004a [FR-006] **Implement calibration‑metric functions**  
  *Implementation file*: `code/eval/metrics.py` (functions: `expected_calibration_error`, `winkler_interval_score`, `sharpness`, `coverage_percentage`, plus decomposition utils).  
  *Verification*: synthetic unit tests for perfect and mis‑calibrated cases.

- [ ] T005a [FR-006] [SC-001] [SC-004] **Compute calibration metrics, reliability diagrams, CV of ECE, and rank methods**  
  *Implementation files*: `code/eval/metrics.py`, `code/eval/ranking.py`, `code/run_seeds.py`  
  *Outputs*:  
    - `results/metrics/calibration_summary.csv` (conforms to `calibration_metric.schema.yaml`, includes `ece_cv`).  
    - Reliability diagram PNGs in `results/reliability_diagrams/`.  
    - `results/best_uq_method.txt` (one of `ensemble`, `mc_dropout`, `sparse_gp`).  
  *Verification*: CSV schema check; CV of ECE across seeds (42, 43, 44) computed and recorded; warning logged if `ece_cv > 0.1`.

---

## Phase 5: Downstream screening case study

- [ ] T006a [FR-007] [SC-003] **Determine screening threshold for fixed recall target**  
  *Implementation file*: `code/eval/screening.py`  
  *Outputs*: `results/screening_threshold.json` (`recall_target`, `threshold_value`).  
  *Verification*: JSON fields numeric; recall constraint satisfied.

- [ ] T006b [FR-007] [SC-003] **Generate baseline (point‑prediction) and random selection CSVs**  
  *Outputs*: `results/screening_baseline.csv`, `results/screening_random.csv`.  
  *Verification*: same number of selected candidates; IDs unique.

- [ ] T006c [FR-007] [SC-003] **UQ‑enhanced selection, precision/recall computation, statistical significance (McNemar)**  
  *Outputs*: `results/screening_candidates.csv`, `results/selection_decisions.csv`, `results/screening_significance.json`, `results/screening_results.csv`.  
  *Verification*: precision gain ≥ 0.05 **or** `p_value < 0.05`; all numeric fields finite.

---

## Phase 6: Runtime enforcement & reporting

- [ ] T007a [FR-009] [SC-002] **Enforce hard 5‑hour wall‑clock limit and record resource usage**  
  *Implementation files*: `code/utils/timeout.py`, integrated in `code/main.py`.  
  *Outputs*: `results/runtime_report.json` (`wall_clock_seconds`, `peak_ram_mb`, `timeout_exceeded`).  
  *Verification*: unit test forces over‑run and expects `TimeoutError`; full pipeline must finish with `timeout_exceeded == false` and `wall_clock_seconds ≤ 18000`.

---

## Phase 7: Final figures, tables & auxiliary validation

- [ ] T008a [SC-001] [SC-003] **Generate final tables & figures from validated outputs**  
  *Implementation files*: `code/visualize/figures.py`, `code/report/tables.py`  
  *Outputs*:  
    - `results/tables/calibration_table.tex` (derived from `calibration_summary.csv`).  
    - `results/figures/aleatoric_epistemic_distribution.png`.  
    - `results/figures/screening_precision_comparison.png`.  
    - `results/tables/screening_summary.csv`.  
  *Verification*: recompute each entry from source CSV/JSON and assert equality within tolerance.

- [ ] T011 [SC-005] [FR-010] **Compute data‑validity metric (null‑value percentage) and store report**  
  *Implementation file*: `code/data/data_validity.py`  
  *Outputs*: `results/data_validity_report.json` (`null_target_percentage`).  
  *Verification*: JSON schema validation; value matches raw dataset statistics.

- [ ] T012 [MaterialSample] **Validate MaterialSample entity against its schema**  
  *Implementation file*: `code/validation/material_sample_schema_check.py`  
  *Outputs*: log confirming all processed samples conform to `dataset.schema.yaml`.  
  *Verification*: schema validator run on a sample of the processed CSVs.

- [ ] T013 [UQPrediction] **Validate UQPrediction outputs against SSoT schema**  
  *Implementation file*: `code/validation/uq_prediction_schema_check.py`  
  *Outputs*: log confirming all prediction CSVs conform to `prediction_output.schema.yaml`.  
  *Verification*: schema validator across all three prediction files.

- [ ] T014 [CalibrationMetric] **Validate CalibrationMetric records against its schema**  
  *Implementation file*: `code/validation/calibration_metric_schema_check.py`  
  *Outputs*: log confirming `calibration_summary.csv` conforms to `calibration_metric.schema.yaml`.  
  *Verification*: schema validator run on the CSV.

---

## Phase 8: Documentation & handoff

- [ ] T009 [P] **Write methods/results account linked to actual outputs**  
  *File*: `specs/001-assessing-uncertainty-quantification-tec/research.md`  
  *Content*: narrative with explicit citations to artifact paths and line numbers (e.g., `calibration_summary.csv: row 3`).  
  *Verification*: lint script checks that every numeric literal appears verbatim in the referenced artifact.

- [ ] T010 [P] **Create quickstart guide & paper‑stage handoff**  
  *File*: `specs/001-assessing-uncertainty-quantification-tec/quickstart.md`  
  *Content*: single command `python -m code.main`, required env vars, expected runtime, and enumeration of all artifacts the paper pipeline will consume.  
  *Verification*: test runs the command on a fresh clone and confirms artifact hashes match recorded values.

---

## Dependencies and requirement coverage

| Spec Requirement | Task(s) | Artifact(s) |
|------------------|---------|--------------|
| FR‑001 | T001a‑T001d | raw download, descriptors, validation_report.json, split CSVs |
| FR‑002 | T002a | baseline_nn_arch.pt |
| FR‑003 | T002b, T003a | ensemble checkpoints, uq_predictions_ensemble.csv |
| FR‑004 | T002c, T003b | mc_dropout checkpoints, uq_predictions_mc_dropout.csv |
| FR‑005 | T001e, T002d, T003c | pca_transformer.pkl, sparse_gp_model.pt, uq_predictions_sparse_gp.csv |
| FR‑006 | T004a, T005a | calibration functions, calibration_summary.csv |
| FR‑007 | T006a‑T006c | screening_threshold.json, screening_* CSVs, screening_results.csv |
| FR‑008 | T003a‑T003c | variance component columns in prediction CSVs |
| FR‑009 | T007a | runtime_report.json |
| FR‑010 | T001c, T011 | validation_report.json, data_validity_report.json |
| SC‑001 | T005a | calibration accuracy metrics |
| SC‑002 | T007a | runtime measurement |
| SC‑003 | T006a‑T006c | screening precision/recall metrics |
| SC‑004 | T005a | `ece_cv` in calibration_summary.csv |
| SC‑005 | T001c, T011 | null‑value percentage report |
| MaterialSample | T001a, T001b, T001c, T001d, T001e, T012 | schema validation log |
| UQPrediction | T013 | schema validation log |
| CalibrationMetric | T014 | schema validation log |

**Execution order**:  
T001a → T001b → T001c → T001d → T001e → T002a → T002b → T002c → T002d → T003a → T003b → T003c → T004a → T005a → T006a → T006b → T006c → T007a → T008a → T011 → T012 → T013 → T014 → T009 → T010.

--- 

*All tasks are unchecked; each will be marked complete only after its artifact(s) exist, pass schema validation, and satisfy the verification steps outlined above.* 