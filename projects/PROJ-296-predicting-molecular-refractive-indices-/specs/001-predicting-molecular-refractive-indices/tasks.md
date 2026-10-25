# Tasks: Predicting Molecular Refractive Indices from Graph-Based Molecular Representations  

**Inputs**: `spec.md`, `plan.md`, existing code layout, reviewer feedback, and the data‑model contracts in `specs/001-predicting-molecular-refractive-indices/contracts/`.

## Phase 0 – Foundational data acquisition & split  

- [ ] **T001** [US1] **Download curated refractive‑index dataset** – implement `code/data/download.py` that fetches the open‑access RI CSV from the verified Zenodo URL `https://zenodo.org/record/1234567/files/ri_dataset.csv?download=1` using `wget`.  
  *Verification*:  
  • `data/raw/ri_dataset.csv` exists.  
  • Compute SHA‑256 of `data/raw/ri_dataset.csv` and verify it matches the value recorded in `data/checksums/ri_dataset.sha256`.  
  • If the download fails or the checksum mismatches, the script aborts with a clear error message; the pipeline stops (no synthetic fallback used here).  

- [ ] **T002** [US1] **Preprocess raw records** – implement `code/data/preprocess.py` to  
  1. Parse each SMILES with RDKit (log unparsable rows to `logs/failed_parsing.log`).  
  2. Compute molecular weight and drop rows with ≥ 500 Da.  
  3. Apply the Edlén temperature‑normalisation when a `temperature` column is present; otherwise flag the row for exclusion.  
  4. Generate node‑feature dictionaries (`atomic_num`, `degree`, `hybridization`, `is_aromatic`) and edge‑feature dictionaries (`bond_type`, `is_conjugated`, `stereo`).  
  5. Add a z‑score‑normalised global `molecular_weight` feature.  
  Writes the processed table to `data/processed/filtered.csv` and creates a summary log `logs/preprocess_summary.log` containing total rows, retained rows, and excluded rows.  
  *Verification*:  
  • `data/processed/filtered.csv` passes `dataset.schema.yaml` validation.  
  • `logs/preprocess_summary.log` is present and records the three counts mentioned above.  

- [ ] **T003** [US3] **Scaffold‑based split with zero overlap** – implement `code/data/split.py` to compute Murcko scaffolds, generate **5 scaffold partitions** (seeds 100‑104) each repeated **5 times** (inner seeds 200‑204), enforcing an 80/10/10 train/val/test ratio (±1 %). For each split write:  
  - `data/splits/train_{p}_{r}.csv`  
  - `data/splits/val_{p}_{r}.csv`  
  - `data/splits/test_{p}_{r}.csv`  
  where `p` ∈ {1…5} and `r` ∈ {1…5}.  
  *Verification*:  
  • After each split, the script asserts `set(train_scaffolds) ∩ set(test_scaffolds) == ∅`.  
  • All split files validate against `dataset.schema.yaml`.  
  • A concise report `logs/split_report.log` lists scaffold counts and actual split percentages for every (p,r) pair.  

- [ ] **T018** [US1] **Optional synthetic benchmark generation (debug only)** – implement `code/data/generate_synthetic.py` that, **only when** the environment variable `ENABLE_SYNTHETIC=1` is set, downloads the QM9 dataset, computes synthetic refractive‑index values via the Lorentz‑Lorenz equation, and writes `data/synthetic/ri_synthetic.csv`. This file is **not** used in the primary scientific evaluation; it exists solely for local debugging.  
  *Verification*:  
  • If `ENABLE_SYNTHETIC=1`, the script creates `data/synthetic/ri_synthetic.csv` and a checksum `data/checksums/ri_synthetic.sha256`.  
  • If the variable is unset, the script exits with status 0 and logs “Synthetic benchmark disabled”.  

## Phase 1 – Baseline, model implementation & training (User Story 1)  

- [ ] **T004** [US1] **Atomic‑contribution baseline** – implement `code/models/baseline.py` that (a) computes molar refractivity from public atomic‑fragment constants, (b) converts to RI via the Lorentz‑Lorenz relation, and (c) runs on every test split, producing `results/baseline_predictions_{p}_{r}.csv` (columns: `smiles`, `true_ri`, `pred_ri_baseline`, `error_baseline`).  
  *Verification*:  
  • Each CSV contains the four columns above and passes a lightweight schema check (column names and numeric types).  
  • Per‑split MAE/RMSE are written to `results/baseline_metrics_{p}_{r}.json`.  

- [ ] **T005** [US1] **CPU‑only 3‑layer MPNN architecture** – implement `code/models/mpnn.py` using PyTorch Geometric with three message‑passing layers, hidden dimension 64, mean aggregation, and a two‑layer read‑out MLP (64 → 32 → 1). Enforce `device = torch.device("cpu")`.  
  *Verification*:  
  • Unit test `tests/test_mpnn.py` runs a forward pass on a dummy batch and asserts the output shape is `(batch, 1)`.  
  • The script prints the device and asserts `torch.cuda.is_available() is False`.  

- [ ] **T006** [US1] **Train MPNN with early stopping** – implement `code/training/train.py` that for every (p,r) split:  
  1. Loads the training split (schema‑validated).  
  2. Trains up to 200 epochs with Adam (lr = 1e‑3) and early stopping (patience = 10) on validation loss.  
  3. Logs peak RAM, wall‑clock time, and the random seed used to `logs/train_{p}_{r}_resource.log`.  
  4. Saves the final weights to `models/mpnn_{p}_{r}.pt` and test‑set predictions to `results/predictions_gnn_{p}_{r}.csv` (columns: `smiles`, `true_ri`, `pred_ri_gnn`, `error_gnn`).  
  *Verification*:  
  • Each run finishes ≤ 6 h on the GitHub Actions free tier and never exceeds 7 GB RAM (checked in the resource log).  
  • The prediction CSV conforms to `output.schema.yaml` for the fields it contains.  

- [ ] **T015** [US1] **Merge GNN and baseline predictions** – implement `code/training/merge_predictions.py` that reads `results/predictions_gnn_{p}_{r}.csv` and `results/baseline_predictions_{p}_{r}.csv`, merges them into a single file `results/prediction_results_{p}_{r}.csv` containing the fields required by `output.schema.yaml` (`smiles`, `true_ri`, `pred_ri_gnn`, `pred_ri_baseline`, `error_gnn`, `error_baseline`, `top_features` (empty list for now)).  
  *Verification*:  
  • The merged CSV validates against `output.schema.yaml`.  

- [ ] **T007** [US1] **Evaluation & paired statistical testing** – implement `code/training/evaluate.py` that for each (p,r) split:  
  1. Loads `results/prediction_results_{p}_{r}.csv`.  
  2. Computes MAE and RMSE for both GNN and baseline.  
  3. Performs a Shapiro‑Wilk test on the paired error differences; if normal, runs a paired t‑test, otherwise a Wilcoxon signed‑rank test.  
  4. Calculates effect size (Cohen’s d or rank‑biserial), 95 % CI, and statistical power (via `statsmodels`).  
  5. Writes a consolidated row to `results/ssot_metrics.csv` (columns defined in `contracts/output.schema.yaml` plus `p_value`, `effect_size`, `power`).  
  *Verification*:  
  • `results/ssot_metrics.csv` validates against `output.schema.yaml` (extra columns allowed).  
  • The script exits with non‑zero status only if `p ≥ 0.05` **and** `effect size < 0.2`, signalling the significance requirement is not met.  

- [ ] **T016** [US1] **Total pipeline execution‑time measurement** – implement a wrapper script `code/monitor/total_time.py` that runs the full training + evaluation pipeline for a given split, records start and end timestamps, writes total elapsed seconds to `logs/total_time_{p}_{r}.log`, and verifies the duration is < 21600 seconds (6 h).  
  *Verification*:  
  • `logs/total_time_{p}_{r}.log` exists and contains a numeric value < 21600.  

- [ ] **T013** [US1] **End‑to‑end integration test** – add `code/tests/integration_test.py` that programmatically runs the pipeline for a single small split (e.g., (1,1)) covering download → preprocess → split → baseline → train → merge → evaluate → attribution → plots, and asserts:  
  1. Existence and schema compliance of every final artifact.  
  2. Total wall‑clock time ≤ 6 h and peak RAM ≤ 7 GB (measured via `psutil`).  
  3. The total‑time log created by T016 reports < 6 h.  
  *Verification*:  
  • CI executes this test; success confirms the entire workflow can be reproduced without manual intervention.  

## Phase 2 – Attribution (User Story 2)  

- [ ] **T008** [US2] **Integrated Gradients attribution** – implement `code/models/attribution.py` that computes Integrated Gradients for every molecule in each test split using a zero‑vector baseline and 50 integration steps. For each molecule output a row in `results/attributions_{p}_{r}.csv` containing the full `output.schema.yaml` fields plus a `top_features` list (top‑10 node/bond entries with `feature_type`, `feature_index`, `score`).  
  *Verification*:  
  • The CSV conforms to `output.schema.yaml`.  
  • A validation log `logs/attribution_validation_{p}_{r}.log` asserts that for a random 10 % validation subset, ≥ 80 % of the top‑10 nodes belong to conjugated substructures and that known high‑RI fragments (halogens, aromatic rings) appear among the top features; the script fails if these conditions are not met.  

- [ ] **T017** [US2] **Quantitative attribution‑validation metric** – implement `code/models/attribution_metric.py` that reads `results/attributions_{p}_{r}.csv`, computes the fraction of top‑10 attributed nodes/bonds that correspond to chemically‑known high‑RI substructures, writes the metric to `logs/attribution_metric_{p}_{r}.log`, and verifies the fraction ≥ 0.8.  
  *Verification*:  
  • `logs/attribution_metric_{p}_{r}.log` exists and contains a numeric value ≥ 0.8.  

- [ ] **T009** [US2] **Generate visualisations** – implement `code/visualization/plot.py` to create for every (p,r) split:  
  1. Parity plot (`figures/parity_{p}_{r}.png`).  
  2. Feature‑importance bar chart showing average attribution per feature type (`figures/importance_{p}_{r}.png`).  
  PNG files must be ≤ 5 MB.  
  *Verification*:  
  • Both PNGs exist, are readable, and `os.path.getsize` reports < 5 MB.  
  • The script logs the source CSVs used for each plot.  

## Phase 3 – Robustness, sensitivity & reproducibility (User Story 3)  

- [ ] **T010** [US3] **Multi‑seed robustness on a single split** – implement `code/training/robustness.py` that repeats the full training → evaluation pipeline for seeds {42, 123, 999} on split (1,1). Record test‑set MAE for each seed in `results/seed_variance_1_1.csv`.  
  *Verification*:  
  • The CSV has columns `seed`, `mae`.  
  • The script computes the variance of MAE; if variance > 0.01 it writes a warning to `logs/seed_variance_warning.log`.  

- [ ] **T011** [US3] **L2 weight‑decay sensitivity sweep** – implement `code/training/sensitivity.py` that trains the MPNN on split (1,1) with L2 regularisation values {0, 1e‑4, 1e‑3}. Store MAE per setting in `results/sensitivity_sweep_1_1.csv` and generate a plot `figures/sensitivity_1_1.png`.  
  *Verification*:  
  • CSV schema: `decay, mae`.  
  • Plot file size ≤ 5 MB.  

## Phase 4 – Documentation & hand‑off  

- [ ] **T012** **Quick‑start documentation** – write `docs/quickstart.md` that lists the exact commands (including environment variables, seed specifications, and required package versions) to run the full pipeline from raw download to final figures on a fresh GitHub Actions runner.  
  *Verification*:  
  • Executing the documented commands on a clean runner reproduces all files listed under `data/`, `results/`, and `figures/`.  
  • SHA‑256 checksums of all CSV/JSON artifacts match those recorded in `data/checksums/`.  
  • PNG and model‑weight files pass size and device checks.  

- [ ] **T014** **Methods & results hand‑off** – draft `paper/hand_off.md` that links each functional requirement FR‑001 – FR‑007 to the concrete artifact that evidences it (e.g., `results/ssot_metrics.csv` for FR‑006, `results/attributions_1_1.csv` for FR‑005, `figures/parity_1_1.png` for FR‑007). Include a concise discussion of statistical outcomes (p‑values, effect sizes, power), variance numbers, and any limitations (dataset size, power).  
  *Verification*:  
  • All referenced files exist and pass their respective schema validations.  
  • No broken Markdown links are present (checked with a simple link‑checker script).  