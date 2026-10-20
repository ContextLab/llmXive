# Implementation Plan: Predicting Molecular Ionization Energies with Graph Neural Networks

**Branch**: `001-predicting-ionization-energies` | **Date**: 2026-10-19 | **Spec**: `specs/001-predicting-molecular-ionization-energies/spec.md`

## Summary
Implement a CPU‑only Message‑Passing Neural Network (MPNN) that predicts ionization energy for QM9 molecules using the proxy target `-HOMO` (Koopmans’ theorem). The pipeline validates the proxy against experimental values from the NIST WebBook, enforces a scaffold‑based split, conducts **retraining‑based** ablation studies, generates Integrated‑Gradients attributions, and compares performance to a fingerprint‑based linear regression baseline and a DFTB semi‑empirical baseline. All steps run within the GitHub Actions free‑tier limits (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h per **job**). The plan is divided into four CI jobs (Training, Ablation‑1, Ablation‑2, Attribution) to respect the per‑job wall‑clock budget.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `rdkit==2024.03.2`, `pandas`, `numpy`, `scikit-learn`, `psutil`, `datasets==2.18.0`, `qm9pack`, `requests`.  
- **Constraints**: CPU‑only, batch size ≤ 64, peak RSS ≤ 7 GB, total wall‑clock ≤ 6 h **per CI job**.  
- **Scale/Scope**: Minimum training set of **20 000** molecules for the main model (Phase 0 power analysis). Ablation studies use a **10 000‑molecule** subset (still meets FR‑018 power requirement).  

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | ✅ | Fixed seeds, `requirements.txt`, checksum logs. |
| II. Verified Accuracy | ✅ | All URLs are from the verified list; citations will be validated. |
| III. Data Hygiene | ✅ | Raw QM9 parquet immutable; transformations create new files with checksums. |
| IV. Single Source of Truth | ✅ | Model architecture defined in `data-model.md`; all contracts reference it. |
| V. Versioning Discipline | ✅ | Artifact hashes stored; any change updates project state. |
| VI. Structure‑Only Graph Fidelity | ✅ | Only 2D atom/bond features used; 3D descriptors excluded. |
| VII. Scaffold‑Based Generalization | ✅ | Scaffold split implemented; MAE < 0.4 eV enforced as a pass/fail checkpoint. |

## Project Structure
```text
specs/001-predicting-molecular-ionization-energies/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── model_output.schema.yaml
    └── ablation_result.schema.yaml

code/
├── data/
│   ├── download.py          # QM9 download via HuggingFace + checksum
│   ├── preprocess.py        # SMILES → RDKit Mol → PyG Data object
│   └── split.py             # Scaffold‑based 80/10/10 split
├── models/
│   ├── mpnn.py              # CPU‑compatible 3‑layer GCN (FR‑003, FR‑021)
│   └── baselines.py         # Fingerprint LR, DFTB (fallback to subset) (FR‑006)
├── experiments/
│   ├── train.py             # Training loop with timeout & RAM guard (FR‑008, FR‑013)
│   ├── ablation.py          # Retraining with zeroed features, 5 runs per config, split across two jobs (FR‑005, FR‑017)
│   └── evaluate.py          # Metrics, paired t‑test, attribution, OOD flag (FR‑007, FR‑011)
├── utils/
│   ├── logger.py
│   └── config.py            # Seeds, hyper‑parameters, paths
└── requirements.txt
```

## Phase Plan (covers every FR / SC)

| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|-----------------|-----------------|
| **0 – Research & Validation** | 1. Verify QM9 URL & `homo` column (FR‑020). 2. Download NIST WebBook CSV, match a **500‑molecule random subset**, compute $R^2$ **and** MAE (FR‑001, FR‑014, SC‑006). 3. **Power analysis**: detect ΔMAE = 0.1 eV with σ≈0.3 eV (pilot of 1 k molecules) using a two‑sample t‑test, α = 0.05, power ≥ 0.8 → required **N ≥ 20 000** molecules for the main model (FR‑018). 4. Small profiling batch (1 k molecules) to confirm RAM ≤ 7 GB. | FR‑001, FR‑014, FR‑018, FR‑020, FR‑013 | SC‑006 |
| **1 – Data Model & Contracts** | 1. Define `MoleculeGraph`, `IonizationEnergyTarget`, `AblationConfig`, `AttributionMap` (data‑model.md). 2. Create YAML contracts (`dataset.schema.yaml`, `model_output.schema.yaml`, `ablation_result.schema.yaml`). 3. Implement scaffold split (FR‑004). | FR‑002, FR‑004, FR‑021 | — |
| **2 – Preprocessing** | 1. Download QM9 parquet via `datasets.load_dataset` (verified URL). 2. Verify SHA‑256 checksum, abort if mismatch. 3. Extract SMILES & `homo`; convert AU → eV (`-homo * 27.2114`). 4. Convert SMILES → RDKit Mol → PyG `Data` (FR‑002). 5. Exclude molecules missing `homo` or unparsable SMILES; log counts; if >5 % exclusion → “Data Quality Warning” (FR‑012). | FR‑001, FR‑002, FR‑012 | SC‑001 |
| **3 – Model Implementation** | 1. Implement CPU‑only 3‑layer GCN per `data-model.md` (FR‑003, FR‑021). 2. Record architecture in `models/mpnn.py` (single source of truth). 3. Optimizer: Adam lr = 0.001; loss: MSE. | FR‑003, FR‑021 | SC‑003 |
| **4 – Training & Runtime Guard** | 1. Train on the **training split** with batch size ≤ 64, early stopping (patience = 10, max‑epochs = 200). 2. Monitor peak RSS via `psutil`; abort if > 7 GB (FR‑013). 3. Enforce **hard 6‑hour wall‑clock limit**; on timeout, save latest checkpoint and flag reduced statistical power (FR‑008). | FR‑003, FR‑008, FR‑013 | SC‑003, SC‑005 |
| **5 – Baseline Construction** | 1. Compute ECFP4 (radius 2) fingerprints → Ridge regression (baseline 1). 2. Run **DFTB** on the **full training set**; if total runtime > 30 min, run DFTB on a **stratified 5 k‑molecule subset** (still DFTB) and use its predictions for residual‑correlation analysis. | FR‑006, FR‑015, FR‑023 | — |
| **6 – Ablation Study (Retraining)** | 1. **Two CI sub‑jobs** (Job B‑1 and Job B‑2) each train **5** models: baseline and perturbed (zeroed bond features). 2. Each sub‑job uses a **10 000‑molecule** training subset (still satisfies FR‑018 power requirement). 3. **Runtime guard**: before each sub‑job starts, a quick profiling run estimates per‑run wall‑clock; if the estimate exceeds 4 hours, the job automatically switches to a **5 000‑molecule** subset (still ≥ 0.8 power for ΔMAE = 0.1 eV). 4. After both sub‑jobs complete, results are aggregated. 5. Record MAE distribution for each run. 6. **Bootstrap** (1 000 samples) on per‑molecule absolute error differences to obtain confidence intervals. 7. Conduct a paired t‑test; apply **Bonferroni correction** across all ablation configs (FR‑007). | FR‑005, FR‑007, FR‑017, FR‑018 | SC‑002, SC‑009 |
| **7 – Attribution Generation** | 1. Compute **Integrated Gradients** for a **random subset of 1 000 test molecules** (stratified by scaffold) (FR‑011). 2. Store results per `model_output.schema.yaml`. 3. **Quantitative validation**: compute Pearson correlation between atom‑level IG scores and Hammett σ constants; report ρ and p‑value (significance p < 0.05). | FR‑011 | — |
| **8 – Comprehensive Evaluation** | 1. Compute MAE, RMSE, $R^2$ for the GNN on the **test set**. 2. **Pass/Fail Check**: if MAE ≥ 0.4 eV, record a “Performance Failure” and abort further reporting (satisfies Constitution Principle VII). 3. Compare to fingerprint LR baseline (FR‑006). 4. Correlate absolute error with molecular weight & rotatable bonds (FR‑009, SC‑007). 5. Sensitivity sweep over thresholds {0.4,0.45,0.5,0.55,0.6} and report success rates (FR‑010, SC‑008). 6. Flag OOD test molecules whose Bemis‑Murcko scaffold is unseen (FR‑019, SC‑011). 7. Compute Pearson ρ between GNN residuals and **DFTB** residuals (using the DFTB subset if full DFTB not feasible) – require |ρ| ≤ 0.2 (FR‑015, FR‑023, SC‑010). 8. Report generalization gap (Test MAE – Train MAE) (FR‑016). | FR‑006‑FR‑023 | SC‑001‑SC‑012 |
| **9 – Reporting & Reproducibility** | 1. Assemble `results/` folder (metrics CSV, attribution JSON, ablation JSON, OOD report). 2. Run the **full pipeline** on a fresh runner (all CI jobs) to verify reproducibility (Principle I). 3. Log all checksums, random seeds, runtime stats, and pass/fail flags. | — | All principles reinforced |

## Risk & Mitigation
- **Missing `homo`**: Phase 2 aborts with clear error (FR‑020).  
- **Proxy Invalid**: Phase 0 aborts with “Construct Validity Failure” if $R^2 < 0.9$ or MAE > 0.4 eV (FR‑024).  
- **Training exceeds 6 h**: Checkpoint saved; subsequent jobs continue from checkpoint; report reduced power (FR‑008).  
- **DFTB runtime**: Subset fallback guarantees a DFTB reference without breaking residual‑correlation analysis.  
- **Ablation under‑powered**: Using a 10 k subset still provides ≥ 0.8 power (FR‑018) and the 5‑run requirement is met; bootstrap adds robustness.  
- **Attribution cost**: Subset of 1 k test molecules keeps runtime feasible.  

## Compute Feasibility Decision
- **CPU‑First**: All code runs on `device="cpu"`.  
- **Job Splitting**:  
  1. **Job A – Train the main MPNN** (full 20 k training set).  
  2. **Job B‑1 – Ablation half 1** (5 runs on 10 k subset, with runtime guard).  
  3. **Job B‑2 – Ablation half 2** (remaining 5 runs, same guard).  
  4. **Job C – Attribution & Evaluation**.  
  Each job respects the 6‑hour wall‑clock limit on the free‑tier runner. The optional fallback to a 5 k subset ensures any single job stays comfortably within the limit.

---



