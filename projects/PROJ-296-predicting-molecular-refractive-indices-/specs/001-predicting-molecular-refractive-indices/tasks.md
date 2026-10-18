# Tasks: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations  

**Inputs**: `spec.md`, `plan.md`, existing code layout, reviewer feedback, and the data‑model contracts in `specs/001-predicting-molecular-refractive-indices/contracts/`.

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] Download the curated refractive‑index dataset as a **CSV** via `wget` from the verified URL, verify its SHA‑256 checksum, and store it under `data/raw/ri_dataset.csv`.   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
  *File*: `code/data/download.py`  
  *Verification*:  
  • Checksum matches the published value (recorded in `state/download_checksum.txt`).  
  • Load the CSV with pandas and validate each row against `contracts/dataset.schema.yaml` (no schema errors).  

- [ ] **T002** [US1] Preprocess raw records: parse SMILES with RDKit, filter molecules with molecular weight ≥ 500 Da, apply temperature normalization (Edlén equation when temperature is present), and generate node/edge features plus a global MW feature. Output processed splits `data/processed/train.csv`, `val.csv`, `test.csv`.  
  *File*: `code/data/preprocess.py`  
  *Verification*:  
  • Log file `logs/preprocess.log` reports counts of total, filtered, and excluded molecules.  
  • All rows in the three CSVs validate against `contracts/dataset.schema.yaml`.  

- [ ] **T003** [US3] Implement a scaffold‑based split (80 % train / 10 % val / 10 % test) with **zero scaffold overlap** and write the split files to `data/processed/`.  
  *File*: `code/data/split.py`  
  *Verification*:  
  • Script prints the number of unique scaffolds per split.  
  • A post‑split check asserts `set(train_scaffolds) ∩ set(test_scaffolds) == ∅` (fails the run if overlap exists).  

- [ ] **T004** [US1] Implement the traditional atomic‑contribution baseline (Molar Refractivity → Lorentz‑Lorenz conversion) and produce baseline predictions for the test set.  
  *File*: `code/models/baseline.py`  
  *Verification*:  
  • Output CSV `results/baseline_predictions.csv` contains columns `smiles`, `true_ri`, `pred_ri_baseline`, `error_baseline`.  
  • Compute MAE and RMSE; both are recorded in `results/baseline_metrics.json`.  

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T005** [US1] Build the 3‑layer Message Passing Neural Network (hidden dimension 64) with **CPU‑only execution** and **pinned random seeds** (e.g., seed=42) logged at start.  
  *File*: `code/models/mpnn.py`  
  *Verification*:  
  • `torch.cuda.is_available()` is asserted to be **False**; the script prints the device used.  
  • Random seeds for `torch`, `numpy`, and `random` are set and logged.  
  • A unit test (`tests/test_mpnn.py`) runs a single forward pass on a dummy batch and checks output shape `(batch, 1)`.  

- [ ] **T006** [US1] Train the MPNN on the processed training split with early stopping (patience = 10), **fixed random seeds**, and explicit CPU‑only enforcement (assert `torch.cuda.is_available() == False` throughout). Log peak RAM, wall‑clock time, and the used seed. Save model weights to `models/mpnn.pt` and test‑set predictions to `results/predictions_gnn.csv`.  
  *File*: `code/training/train.py`  
  *Verification*:  
  • Run finishes within **6 h** on the GitHub Actions free tier and never exceeds **7 GB** RAM (recorded in `logs/train_resource_usage.log`).  
  • `results/predictions_gnn.csv` contains `smiles`, `true_ri`, `pred_ri_gnn`, `error_gnn`.  
  • The script asserts `torch.cuda.is_available() == False` for the whole training loop.  

- [ ] **T007** [US1] Evaluate both GNN and baseline on the test set, compute MAE & RMSE, perform a normality check (Shapiro‑Wilk) on paired error differences, and run a paired t‑test or Wilcoxon signed‑rank test as appropriate. Store all metrics in `results/metrics.csv`.  
  *File*: `code/training/evaluate.py`  
  *Verification*:  
  • `results/metrics.csv` conforms to `contracts/output.schema.yaml`.  
  • The script prints the test used, the p‑value, Cohen’s d, and a 95 % confidence interval.  

- [ ] **T008** [US2] Apply Integrated Gradients to the trained MPNN for every molecule in the test set, using a zero‑vector baseline and 50 integration steps. Export per‑molecule attributions to `results/attributions.csv`.  
  *File*: `code/models/attribution.py`  
  *Verification*:  
  • Each row includes `smiles`, `node_attributions`, `edge_attributions`, and a `top_features` list (top 10).  
  • For a held‑out validation subset enriched in conjugated π‑systems, at least **80 %** of the top‑10 attributed nodes belong to conjugated substructures (asserted in `logs/attribution_validation.log`).  

- [ ] **T009** [US2] Generate visualisations: (a) parity plot (predicted vs. actual RI) and (b) feature‑importance bar chart (average attribution per feature type). Save as PNGs `figures/parity.png` and `figures/importance.png`, each **< 5 MB**.  
  *File*: `code/visualization/plot.py`  
  *Verification*:  
  • File size checks (`os.path.getsize`) confirm the < 5 MB constraint.  
  • Plots are reproducible from the CSVs in `results/`.  

- [ ] **T010** [US3] Conduct multi‑seed robustness experiments (seeds = 42, 123, 999). For each seed, retrain the MPNN and record test‑set MAE. Summarise variance in `results/seed_variance.csv`.  
  *File*: `code/training/robustness.py`  
  *Verification*:  
  • Variance of MAE across the three seeds is ≤ 0.01; if higher, the script flags a warning and the variance value is reported.  

- [ ] **T011** [US3] Perform a lightweight hyper‑parameter sensitivity sweep on L2 weight‑decay (values = 0, 1e‑4, 1e‑3). Record MAE for each setting in `results/sensitivity_sweep.csv` and plot MAE vs. decay in `figures/sensitivity.png`.  
  *File*: `code/training/sensitivity.py`  
  *Verification*:  
  • Plot file size < 5 MB; CSV conforms to a simple schema (`decay, mae`).  

- [ ] **T015** [US1] **Contract Validation** – After each major pipeline stage (download, preprocessing, baseline, GNN training, evaluation, attribution), run a schema validation step against the appropriate contract (`dataset.schema.yaml` or `output.schema.yaml`). Abort on any validation failure.  
  *File*: `code/validation/validate_contracts.py`  
  *Verification*:  
  • Validation script exits with status 0 only if all files pass; logs detailed errors otherwise.  

- [ ] **T016** [US3] **Entity Usage Traceability** – Verify that each pipeline component consumes and produces the defined entities (`MoleculeGraph`, `PredictionResult`, `FeatureAttribution`) as specified in `data-model.md`. Generate a traceability report `logs/entity_traceability.log`.  
  *File*: `code/validation/trace_entities.py`  
  *Verification*:  
  • Report lists each stage’s input and output entity types; CI fails if any mismatch is detected.  

- [ ] **T017** [US2] **External Attribution Validation** – Compare attribution scores for a curated benchmark set of molecules against independent physical measurements (e.g., literature polarizability contributions). Compute correlation (Pearson r) and report significance; require r ≥ 0.6 or flag as limitation.  
  *File*: `code/models/external_attribution_check.py`  
  *Verification*:  
  • Generates `results/attribution_external_validation.csv` with correlation metrics and a pass/fail flag.  

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T012** Write a **quick‑start** guide (`docs/quickstart.md`) that lists the exact commands to reproduce the full pipeline from raw download to final figures, including required environment variables and seed settings.  
  *Verification*:  
  • Running the documented commands on a fresh runner reproduces all files listed in `results/` and `figures/` with identical checksums.  

- [ ] **T013** Draft a **methods & results hand‑off** (`paper/hand_off.md`) that links each scientific requirement (FR‑001 – FR‑007) to the concrete artifact that evidences it, cites the statistical test outcomes, and notes any limitations (e.g., power analysis shortfall).  
  *Verification*:  
  • The hand‑off references every CSV/PNG produced above and includes the p‑value, effect size, and variance numbers.  

- [ ] **T014** Add integration tests (`code/tests/integration_test.py`) that automatically verify the end‑to‑end data flow: download → preprocess → split → baseline → GNN training → evaluation → attribution → plots. The test asserts the existence and schema compliance of all final artifacts.  
  *Verification*:  
  • CI runs the integration test; success means the full pipeline can be executed without manual intervention.  

---  

### Requirement coverage mapping  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| **FR‑001** (dataset download & preprocessing) | T001, T002 |
| **FR‑002** (CPU‑only 3‑layer MPNN) | T005, T006 |
| **FR‑003** (scaffold split) | T003 |
| **FR‑004** (atomic‑contribution baseline) | T004 |
| **FR‑005** (Integrated Gradients) | T008 |
| **FR‑006** (MAE/RMSE & paired test) | T007 |
| **FR‑007** (Parity & importance plots) | T009 |
| **User Story 1** (CPU feasibility, baseline comparison) | T001‑T007 |
| **User Story 2** (feature attribution) | T008‑T009, T017 |
| **User Story 3** (robustness & sensitivity) | T010‑T011 |
| **Additional compliance** | T015 (contract validation), T016 (entity traceability) |