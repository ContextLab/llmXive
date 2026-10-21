# Tasks: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations  

**Inputs**: `spec.md`, `plan.md`, existing code layout, reviewer feedback, and the data‑model contracts in `specs/001-predicting-molecular-refractive-indices/contracts/`.

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] **T001** [US1] **Download curated refractive‑index dataset** – implement `code/data/download.py` that fetches the open‑access RI dataset using `wget` from the specified canonical URL.   <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1; code/data/preprocess.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download.py exit=1 -->
  *File*: `code/data/download.py`  
  *Verification*:  
  • The script writes `data/raw/ri_dataset.csv` and a SHA‑256 checksum file `state/ri_dataset.sha256`.  
  • Verify checksum matches the value recorded in `state/ri_dataset.sha256`.  
  • Load the CSV with `pandas` and run schema validation against `contracts/dataset.schema.yaml` – the script must exit with status 0 only if no validation errors are found.

- [ ] **T002** [US1] **Preprocess raw records** – implement `code/data/preprocess.py` to:
  1. Parse each SMILES with RDKit, logging unparsable entries to `logs/failed_parsing.log`.  
  2. Compute molecular weight and drop rows with ≥ 500 Da.  
  3. Apply temperature normalisation (Edlén equation) when a temperature column is present; otherwise flag the row for exclusion.  
  4. Generate node features (`atomic_num`, `degree`, `hybridization`, `is_aromatic`) and edge features (`bond_type`, `is_conjugated`, `stereo`).  
  5. Add a z‑score‑normalised global `molecular_weight` feature.  
  *File*: `code/data/preprocess.py`  
  *Verification*:  
  • Output `data/processed/filtered.csv`.  
  • `logs/preprocess_summary.log` records total rows, filtered rows, and excluded rows.  
  • All rows in `filtered.csv` must pass `contracts/dataset.schema.yaml` validation.

- [ ] **T003** [US3] **Scaffold‑based split with zero overlap** – implement `code/data/split.py` to compute Murcko scaffolds, generate **5 random scaffold splits** (seed 100‑104) each repeated **5 times** (inner seed 200‑204), strictly enforcing an **80/10/10 train/val/test ratio**. For each split write `data/splits/train_{i}_{j}.csv`, `val_{i}_{j}.csv`, `test_{i}_{j}.csv` (i = 1..5, j = 1..5).   <!-- FAILED-IN-EXECUTION: code/data/split.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/split.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/split.py exit=1 -->
  *File*: `code/data/split.py`  
  *Verification*:  
  • After each split the script prints the number of unique scaffolds per split and the actual split ratios.  
  • An assertion aborts the run if `set(train_scaffolds) ∩ set(test_scaffolds) != ∅` or if ratios deviate from 80/10/10 by more than 1%.  
  • All split files validate against `contracts/dataset.schema.yaml`.

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T004** [US1] **Atomic‑contribution baseline** – implement `code/models/baseline.py` that computes molar refractivity from atomic fragment constants (public tables) and converts to RI via the Lorentz‑Lorenz relation. Run baseline on every test split and write `results/baseline_predictions_{i}_{j}.csv`.  
  *File*: `code/models/baseline.py`  
  *Verification*:  
  • Each CSV contains columns `smiles`, `true_ri`, `pred_ri_baseline`, `error_baseline`.  
  • Compute MAE and RMSE per split and store in `results/baseline_metrics_{i}_{j}.json`.

- [ ] **T005** [US1] **CPU‑only 3‑layer MPNN architecture** – implement `code/models/mpnn.py` using PyTorch Geometric with three message‑passing layers, hidden dimension 64, mean aggregation, and a two‑layer read‑out MLP (64 → 32 → 1). Enforce `device = torch.device("cpu")`.  
  *File*: `code/models/mpnn.py`  
  *Verification*:  
  • Unit test `tests/test_mpnn.py` runs a forward pass on a dummy batch and checks output shape `(batch, 1)`.  
  • The script prints the device being used and asserts `torch.cuda.is_available() is False`.

- [ ] **T006** [US1] **Train MPNN with early stopping** – implement `code/training/train.py` that:  
  1. Loads a training split, validates schema, and trains for up to 200 epochs with Adam (lr = 1e‑3).  
  2. Uses early stopping (patience = 10) on validation loss.  
  3. Logs peak RAM, wall‑clock time, and random seed used.  
  4. Saves model weights to `models/mpnn_{i}_{j}.pt` and test‑set predictions to `results/predictions_gnn_{i}_{j}.csv`.  
  *File*: `code/training/train.py`  
  *Verification*:  
  • Each run finishes ≤ 6 h on the GitHub Actions free tier and never exceeds 7 GB RAM (recorded in `logs/train_{i}_{j}_resource.log`).  
  • Prediction CSV contains `smiles`, `true_ri`, `pred_ri_gnn`, `error_gnn`.  
  • The script asserts `torch.cuda.is_available() is False` throughout.

- [ ] **T007** [US1] **Evaluation & statistical testing** – implement `code/training/evaluate.py` to:  
  1. Load GNN and baseline predictions for a given split.  
  2. Compute MAE, RMSE for both.  
  3. Perform Shapiro‑Wilk normality test on the paired error differences; if normal, run a paired t‑test, otherwise run Wilcoxon signed‑rank test.  
  4. Record p‑value, Cohen’s d, 95 % CI, and the test used.  
  *File*: `code/training/evaluate.py`  
  *Verification*:  
  • Output `results/metrics_{i}_{j}.csv` conforms to `contracts/output.schema.yaml`.  
  • Console prints the statistical summary; the script exits with non‑zero status if p ≥ 0.05 **and** the effect size is negligible (Cohen’s d < 0.2), signalling a failed significance requirement.

- [ ] **T008** [US2] **Integrated Gradients attribution** – implement `code/models/attribution.py` that computes IG for every molecule in the test set using a zero‑vector baseline and 50 integration steps. Export per‑molecule attributions to `results/attributions_{i}_{j}.csv` matching `output.schema.yaml`.  
  *File*: `code/models/attribution.py`  
  *Verification*:  
  • Each row contains `smiles`, `true_ri`, `pred_ri_gnn`, `error_gnn`, and a `top_features` list of the 10 highest‑scoring node/bond entries (fields `feature_type`, `feature_index`, `score`).  
  • **External Validation**: For a validation subset, a post‑hoc check in `logs/attribution_validation_{i}_{j}.log` asserts that ≥ 80 % of top‑10 nodes belong to conjugated substructures AND that top-scoring features correlate with known high-RI fragments (e.g. halogens, aromatic rings) from established literature; the script fails if these conditions are not met.

- [ ] **T009** [US2] **Generate visualisations** – implement `code/visualization/plot.py` to create:  
  1. Parity plot (predicted vs. actual RI) → `figures/parity_{i}_{j}.png`.  
  2. Feature‑importance bar chart (average attribution per feature type) → `figures/importance_{i}_{j}.png`.  
  *File*: `code/visualization/plot.py`  
  *Verification*:  
  • Each PNG size ≤ 5 MB (checked via `os.path.getsize`).  
  • Plots are reproducible from the corresponding CSVs; the script logs the source files used.

- [ ] **T010** [US3] **Multi‑seed robustness** – implement `code/training/robustness.py` that repeats the entire training‑evaluation pipeline for seeds {42, 123, 999} on a single scaffold split (e.g., split 1‑1). Record test‑set MAE for each seed in `results/seed_variance_1_1.csv`.  
  *File*: `code/training/robustness.py`  
  *Verification*:  
  • Compute variance of MAE across the three seeds; if variance > 0.01, the script writes a warning to `logs/seed_variance_warning.log`.  
  • The CSV contains columns `seed`, `mae`.

- [ ] **T011** [US3] **L2 weight‑decay sensitivity sweep** – implement `code/training/sensitivity.py` to train the MPNN on a fixed split (1‑1) with L2 values {0, 1e‑4, 1e‑3}. Store MAE per setting in `results/sensitivity_sweep_1_1.csv` and plot `figures/sensitivity_1_1.png`.  
  *File*: `code/training/sensitivity.py`  
  *Verification*:  
  • CSV schema: `decay, mae`.  
  • Plot file size ≤ 5 MB.

- [ ] **T012** **Contract validation pipeline** – implement `code/validation/validate_contracts.py` that is invoked after every major stage (download, preprocess, split, baseline, training, evaluation, attribution). It validates the newly created files against the appropriate JSON‑Schema, **computes SHA‑256 content hashes for every produced artifact**, and records them in `state/artifact_hashes.json`. It aborts on failure, logging details to `logs/validation_{stage}.log`.  
  *File*: `code/validation/validate_contracts.py`  
  *Verification*:  
  • Returns exit code 0 only when all files pass and hashes are recorded; CI fails otherwise.

- [ ] **T013** **Entity traceability report** – implement `code/validation/trace_entities.py` that reads the pipeline configuration, tracks the input and output entity types (`MoleculeGraph`, `PredictionResult`, `FeatureAttribution`) for each script, and writes a human‑readable report `logs/entity_traceability.log`.  
  *File*: `code/validation/trace_entities.py`  
  *Verification*:  
  • CI step fails if any stage consumes or produces an entity not defined in `data-model.md`.

- [ ] **T014** **Quick‑start documentation** – write `docs/quickstart.md` that lists the exact commands (with environment variables, seeds, and required package versions) to run the full pipeline from raw download to final figures on a fresh runner.  
  *Verification*:  
  • Executing the documented commands on a clean GitHub Actions runner reproduces all files listed in `results/` and `figures/`.  
  • **Deterministic Check**: CSV and JSON artifacts must have identical SHA‑256 checksums; PNG and PT files must pass schema/size checks.

- [ ] **T015** **Methods & results hand‑off** – draft `paper/hand_off.md` linking each functional requirement FR‑001 – FR‑007 to the concrete artifact that evidences it (e.g., `results/metrics_1_1.csv` for FR‑006). Include statistical test outcomes (p‑values, effect sizes), variance numbers, and a concise discussion of limitations (e.g., dataset size, power).  
  *Verification*:  
  • All referenced artifacts exist and pass schema validation; the document contains no broken links.

- [ ] **T016** **End‑to‑end integration test** – add `code/tests/integration_test.py` that programmatically runs the whole pipeline (download → preprocess → split → baseline → train → evaluate → attribution → plots) for a single small split (e.g., split 1‑1) and asserts the existence and schema compliance of every final artifact.  
  *File*: `code/tests/integration_test.py`  
  *Verification*:  
  • CI executes this test; success means the pipeline can be reproduced without manual intervention.  
  • **Success Criteria Assertion**: The script must measure and assert that total wall-clock time is ≤ 6h (SC-004) and peak RAM usage is ≤ 7GB (SC-005).

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
| **User Story 1** (CPU feasibility, baseline comparison) | T001‑T007, T016 |
| **User Story 2** (feature attribution) | T008‑T009 |
| **User Story 3** (robustness & sensitivity) | T010‑T011 |
| **Additional compliance** | T012 (contract validation), T013 (entity traceability) |
| **Paper hand‑off** | T014‑T015 |
| **Reproducibility** | T016 |

---  

*All tasks are expressed as unchecked check‑boxes; they will be marked complete only after the corresponding script runs successfully and the verification steps pass.*