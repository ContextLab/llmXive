# Tasks: Predicting Molecular Ionization Energies with Graph Neural Networks  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and reviewer feedback.  

The list below follows the canonical `- [ ] T### [P?] [USx?] description …` format, groups related work into logical phases, and records the exact verification steps required for each scientific requirement.

---  

## Phase 1 – Setup, data provenance & construct‑validity gating  

- [ ] **T001** [P1] [US-1] Verify external data sources and compute proxy‑validation metrics.  
  - **File(s)**: `code/data/download.py`, `code/data/validate_proxy.py`  
  - **Actions**:  
    1. Download QM9 from `https://huggingface.co/datasets/deepchem/qm9` and verify SHA‑256 checksum.  
    2. Download experimental ionization energies (NIST WebBook CSV) and verify URL/metadata (FR‑026).  
    3. Randomly sample **500** molecules, compute `-homo * 27.2114` (eV) and compare against NIST values.  
    4. Calculate **R²** and **MAE**; require `R² ≥ 0.9` **and** `MAE ≤ 0.4 eV`.  
  - **Verification**: Unit test (`tests/test_proxy_validation.py`) asserts both thresholds; pipeline aborts with “Construct Validity Failure” if not met (FR‑024).  

- [ ] **T002** [P1] [US-1] Preprocess QM9 into 2‑D graph objects and enforce data‑quality rules.  
  - **File(s)**: `code/data/preprocess.py`  
  - **Actions**:  
    1. Load QM9 parquet, extract SMILES and `homo`.  
    2. Convert SMILES → RDKit `Mol`; drop molecules where RDKit parsing fails or `homo` is missing.  
    3. Log count of excluded molecules; if > 5 % emit a “Data Quality Warning” (FR‑012).  
    4. Store processed graphs as `data/processed/graphs.pt` and write a manifest `data/processed/manifest.csv`.  
  - **Verification**: Test (`tests/test_preprocess.py`) checks that the manifest contains ≥ 10 000 training molecules after exclusion and that the warning flag is raised when appropriate.  

- [ ] **T003** [P1] [US-1] Perform scaffold‑based split with covariate balance checks.  
  - **File(s)**: `code/data/split.py`  
  - **Actions**:  
    1. Generate Bemis‑Murcko scaffolds, assign 80 %/10 %/10 % to train/val/test.  
    2. Verify that training set size ≥ 10 000 molecules.  
    3. Compute balance metrics for molecular weight and rotatable bonds; if any scaffold‑level imbalance > 10 % re‑split stratified by those properties.  
    4. Save split indices to `data/splits/{train,val,test}.pt`.  
  - **Verification**: Test (`tests/test_split.py`) asserts split sizes, scaffold disjointness, and that the balance flag is false for the final split.  

---  

## Phase 2 – Model implementation, main training & baseline construction  

- [ ] **T004** [P2] [US-2] Implement the CPU‑only MPNN architecture and record it as the single source of truth.  
  - **File(s)**: `code/models/mpnn.py`  
  - **Actions**:  
    1. Define a 3‑layer GCN with hidden dimension 64, edge embedding 32, global‑average readout, and ReLU activations (FR‑003, FR‑021).  
    2. Include a JSON/YAML block documenting architecture (layer types, depths, hidden sizes).  
  - **Verification**: Test (`tests/test_mpnn_architecture.py`) loads the class, inspects the `__dict__` for the documented parameters, and confirms `device="cpu"` by default.  

- [ ] **T005** [P2] [US-2] Train the baseline MPNN on the full training split within the 6‑hour wall‑clock and 7 GB RAM limits.  
  - **File(s)**: `code/experiments/train.py`  
  - **Actions**:  
    1. Load training loader (batch ≤ 64).  
    2. Train up to 200 epochs with early stopping (patience = 10) and a hard timeout of 6 h; on timeout save the latest checkpoint (`code/models/checkpoint_latest.pth`).  
    3. Monitor peak RSS via `psutil`; abort if > 7 GB (FR‑013).  
    4. Record final training MAE and RAM usage in `results/training_log.json`.  
  - **Verification**: Integration test (`tests/test_training_timeout.py`) simulates a short timeout and checks that a checkpoint is written and that the log contains `timeout: true` when appropriate.  

- [ ] **T006** [P3] [US-3] Build the fingerprint‑based linear‑regression baseline (ECFP4, radius 2).  
  - **File(s)**: `code/models/baselines.py`  
  - **Actions**:  
    1. Compute ECFP4 for every molecule in train/val/test.  
    2. Fit Ridge regression on the training set, evaluate on test.  
    3. Store baseline predictions in `results/baseline_predictions.csv`.  
  - **Verification**: Test (`tests/test_baseline.py`) asserts that the baseline MAE is computed and saved, and that the file header matches `model_output.schema.yaml`.  

---  

## Phase 3 – Ablation studies (retraining) & attribution  

- [ ] **T007** [P2] [US-2] Implement retraining‑based ablation pipeline for zeroing structural features.  
  **File(s)**: `code/experiments/ablation.py`  
  - **Actions**:  
    1. Define `AblationConfig` objects for each target feature (e.g., `bond_type`, `atom_type`).  
    2. For each config, run **3** stochastic trainings (different seeds, same split) with the selected feature zeroed out during data loading.  
    3. Record per‑run MAE in `results/ablation/{feature}_run{i}.json`.  
    4. Enforce `num_runs == 3` (FR‑017).  
  - **Verification**: Test (`tests/test_ablation_runs.py`) checks that exactly three result files exist per config and that each contains a numeric `mae`.  

- [ ] **T008** [P2] [US-2] Perform paired statistical testing on each ablation configuration.  
  - **File(s)**: `code/experiments/statistics.py`  
  - **Actions**:  
    1. Load baseline per‑molecule absolute errors and perturbed per‑molecule absolute errors (same random seed ensures pairing).  
    2. Run Shapiro‑Wilk; if normality rejected, switch to Wilcoxon signed‑rank.  
    3. Apply Bonferroni correction across all configs.  
    4. Compute **p‑value**, **Cohen’s d**, and post‑hoc power; store results in `results/ablation/{feature}_stats.json` adhering to `ablation_result.schema.yaml`.  
  - **Verification**: Test (`tests/test_ablation_stats.py`) validates schema compliance and that `is_significant` matches the corrected p‑value threshold.  

- [ ] **T009** [P2] [US-2] Generate Integrated‑Gradients attribution maps for a stratified subset of 1 000 test molecules.  
  - **File(s)**: `code/experiments/attribution.py`  
  - **Actions**:  
    1. Select 1 000 test molecules stratified by scaffold.  
    2. Compute IG scores for each atom/bond, normalize with min‑max, and store as `AttributionMap` objects in `results/attribution/{molecule_id}.json`.  
    3. Perform a qualitative validation: check that high‑score atoms belong to hetero‑atoms or conjugated systems; log any major discrepancies (FR‑022).  
  - **Verification**: Test (`tests/test_attribution.py`) confirms that each JSON file matches `model_output.schema.yaml` and that the qualitative check writes a summary `results/attribution/validation_report.txt`.  

---  

## Phase 4 – Comprehensive evaluation & reporting  

- [ ] **T010** [P3] [US-3] Evaluate the trained GNN on the test set and compare to baseline.  
  - **File(s)**: `code/experiments/evaluate.py`  
  - **Actions**:  
    1. Compute **MAE**, **RMSE**, and **R²** for the GNN and for the fingerprint baseline (FR‑006).  
    2. Record the **generalization gap** = `Test MAE – Train MAE` (must be ≤ 0.05 eV, SC‑004).  
    3. Save a consolidated table `results/metrics.csv`.  
  - **Verification**: Test (`tests/test_metrics.py`) asserts that the CSV contains the required columns and that the gap column meets the threshold; otherwise the test fails.  

- [ ] **T011** [P3] [US-3] Correlate prediction error with molecular properties and perform sensitivity analysis on the success threshold.  
  - **File(s)**: `code/experiments/error_analysis.py`  
  - **Actions**:  
    1. Compute Pearson ρ between absolute error and (a) molecular weight, (b) number of rotatable bonds (FR‑009). Acceptable |ρ| ≤ 0.3 or p > 0.05 (SC‑007).  
    2. Sweep the “acceptable‑prediction” threshold over `{0.4, 0.45, 0.5, 0.55, 0.6}` eV; record success rate for each and ensure variation ≤ ±5 % (SC‑008).  
    3. Output `results/error_property_correlation.json` and `results/threshold_sensitivity.csv`.  
  - **Verification**: Test (`tests/test_error_analysis.py`) checks that both correlation values and the sensitivity CSV exist and that the variation constraint holds.  

- [ ] **T012** [P3] [US-3] OOD detection and residual‑overlap analysis.  
  - **File(s)**: `code/experiments/ood_analysis.py`  
  - **Actions**:  
    1. Flag test molecules whose Bemis‑Murcko scaffold does not appear in the training split; write count & proportion to `results/ood_report.json` (must be ≤ 10 %).  
    2. Compute Pearson ρ between GNN residuals and DFTB residuals on the overlapping subset; require |ρ| ≤ 0.2 (FR‑015, FR‑023, SC‑010).  
    3. Store both results in `results/ood_and_residuals.json`.  
  - **Verification**: Test (`tests/test_ood_analysis.py`) validates schema, proportion limit, and correlation threshold.  

- [ ] **T013** [P3] Compile a reproducible results package and handoff to the paper stage.  
  - **File(s)**: `results/` (all CSV/JSON artifacts), `quickstart.md` (command summary).  
  - **Actions**:  
    1. Run the full pipeline on a fresh runner (`./run_pipeline.sh`) and confirm that all tasks from T001–T012 complete without error.  
    2. Record checksums of every artifact, the random seeds used, and the wall‑clock time of each CI job.  
    3. Write `research_handoff.md` linking each result file to the corresponding scientific requirement (FR/SC).  
  - **Verification**: Integration test (`tests/test_full_pipeline.py`) executes the script, parses `research_handoff.md`, and asserts that every FR referenced has a matching entry with a passing metric.  

---  

## Phase 5 – Optional power‑analysis re‑evaluation (fallback handling)  

- [ ] **T014** [P2] Re‑estimate statistical power if any job is forced to use a reduced molecule subset (e.g., due to timeout).  
  - **File(s)**: `code/utils/power_analysis.py`  
  - **Actions**:  
    1. Given the actual training size `N`, compute achieved power for detecting ΔMAE = 0.1 eV with σ≈0.3 eV at α = 0.05.  
    2. If power < 0.8, abort the remaining pipeline and emit a “Insufficient Power” report.  
  - **Verification**: Test (`tests/test_power_analysis.py`) checks that the function returns a float ≥ 0.8 for the default `N = 20 000` and correctly flags lower `N`.  

---  

### Dependency & Requirement Coverage  

| Requirement | Satisfied by Task(s) |
|-------------|----------------------|
| FR‑001, FR‑014, SC‑006 | T001 |
| FR‑002, FR‑012 | T002 |
| FR‑004 | T003 |
| FR‑003, FR‑021 | T004 |
| FR‑008, FR‑013, SC‑003, SC‑005 | T005 |
| FR‑006 | T006 |
| FR‑005, FR‑017, FR‑018, SC‑009 | T007 |
| FR‑007, FR‑017 | T008 |
| FR‑011, FR‑022 | T009 |
| FR‑006, FR‑016, SC‑004 | T010 |
| FR‑009, FR‑010, SC‑007, SC‑008 | T011 |
| FR‑015, FR‑019, FR‑023, SC‑010, SC‑011 | T012 |
| FR‑025 (CI orchestration) | Implicitly across all CI‑job tasks (T001‑T014) |
| FR‑026 | T001 (URL verification) |
| FR‑024 (abort on invalid proxy) | T001 |
| FR‑020 (schema verification) | T002 (checks column existence) |
| FR‑021 (architecture single source) | T004 |
| FR‑018 (power analysis) | T014 (fallback) |
| … (all other FR/SC) | Covered as indicated above |

---  

*All tasks are unchecked; the runtime will mark them as completed only after the corresponding verification passes.*
