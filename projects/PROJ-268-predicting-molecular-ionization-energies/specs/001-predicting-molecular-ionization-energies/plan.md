# Implementation Plan: Predicting Molecular Ionization Energies with Graph Neural Networks

**Branch**: `001-predicting-ionization-energies` | **Date**: 2026-10-24 | **Spec**: `specs/001-predicting-molecular-ionization-energies/spec.md`

## Summary
Implement a CPU‑only Message‑Passing Neural Network (MPNN) that predicts ionization energy for QM9 molecules using the proxy target `-HOMO` (Koopmans’ theorem). The pipeline validates the proxy against experimental values from the NIST WebBook, enforces a scaffold‑based split, conducts retraining‑based ablation studies, generates Integrated‑Gradients attribution maps, and compares performance to a fingerprint‑based linear regression baseline and a DFTB semi‑empirical baseline. All steps run within the GitHub Actions free‑tier limits (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h per CI job).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch-geometric==2.5.3`, `rdkit==2024.03.2`, `pandas`, `numpy`, `scikit-learn`, `psutil`, `datasets==2.18.0`, `qm9pack`, `requests`.  
- **Constraints**: CPU‑only, batch size ≤ 64, peak RSS ≤ 7 GB, per‑job wall‑clock ≤ 6 h.  
- **Scale/Scope**: Minimum training set of **20 000** molecules for the full model (derived from a priori power analysis). Ablation studies use a **10 000‑molecule** subset (meets power requirements; fallback to 5 000‑molecule subset only if power re‑estimation still ≥ 0.8).

## Constitution Check
| Principle | Status | Action |
|-----------|--------|--------|
| I. Reproducibility | ✅ | Fixed seeds, `requirements.txt`, checksum logs. |
| II. Verified Accuracy | ✅ | Added explicit URL and citation verification against primary sources in Phase 0 (see below). |
| III. Data Hygiene | ✅ | Raw QM9 parquet immutable; transformations create new files with checksums. |
| IV. Single Source of Truth | ✅ | Model architecture defined in `models/mpnn.py`; all contracts reference it. |
| V. Versioning Discipline | ✅ | Artifact hashes stored; any change updates project state. |
| VI. Structure‑Only Graph Fidelity | ✅ | Only 2D atom/bond features used; no 3D descriptors. |
| VII. Scaffold‑Based Generalization | ✅ | Scaffold split implemented; MAE < 0.4 eV enforced as a pass/fail checkpoint. |
| **FR‑024** (Construct‑Validity Gating) | ✅ | Added explicit gating step in Phase 0; training aborts if proxy validation fails. |
| **FR‑025** (CI Job Orchestration) | ✅ | Detailed CI job breakdown in Phase 10, each respecting the 6‑hour limit. |

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
│   ├── download.py          # QM9 download via `qm9pack` + checksum
│   ├── preprocess.py        # SMILES → RDKit Mol → PyG Data
│   └── split.py             # Scaffold‑based 80/10/10 split
├── models/
│   ├── mpnn.py              # CPU‑compatible 3‑layer GCN (FR‑003, FR‑021)
│   └── baselines.py         # Fingerprint LR & DFTB (FR‑006, FR‑015, FR‑023)
├── experiments/
│   ├── train.py             # Training loop with timeout & RAM guard (FR‑008, FR‑013)
│   ├── ablation.py          # Retraining with zeroed bond features, 5 runs per config (FR‑005, FR‑017)
│   └── evaluate.py          # Metrics, paired t‑test, attribution, OOD flag (FR‑007, FR‑011, FR‑019)
├── utils/
│   ├── logger.py
│   └── config.py            # Seeds, hyper‑parameters, paths
└── requirements.txt
```

## Phase Plan (covers every FR / SC)

| Phase | Tasks | FR(s) Addressed | SC(s) Addressed |
|-------|-------|-----------------|-----------------|
| **0 – Research & Validation** | 1. Verify QM9 URL, NIST WebBook URL, and column schema against primary sources (Principle II). 2. Compute SHA‑256 checksums for QM9 and NIST files; abort on mismatch. 3. Download NIST WebBook CSV, match a **500‑molecule random subset**, compute $R^2$ **and** MAE (FR‑001, FR‑014, SC‑006). 4. **Construct‑Validity Gating** (FR‑024): if $R^2<0.9$ **or** MAE > 0.4 eV, abort the entire pipeline with a “Construct Validity Failure” report. 5. Perform a priori power analysis (α = 0.05, desired power ≥ 0.8) to detect ΔMAE = 0.1 eV with σ≈0.3 eV, yielding required **N ≥ 20 000** for the full model (FR‑018). 6. Profile a 1 k‑molecule batch to confirm RAM ≤ 7 GB (FR‑013). | FR‑001, FR‑014, FR‑018, FR‑020, FR‑013, FR‑024, Principle II | SC‑006 |
| **1 – Data Model & Contracts** | 1. Define `MoleculeGraph`, `IonizationEnergyTarget` (field `negative_homo_proxy`), `AblationConfig`, `AttributionMap` (data‑model.md). 2. Create YAML contracts (`dataset.schema.yaml`, `model_output.schema.yaml`, `ablation_result.schema.yaml`). 3. Implement scaffold split (FR‑004). | FR‑002, FR‑004, FR‑021 | — |
| **2 – Preprocessing** | 1. Load QM9 via `qm9pack` (verified source). 2. Verify checksum; abort on mismatch. 3. Extract SMILES & `homo`; convert AU → eV (`-homo * 27.2114`). 4. Convert SMILES → RDKit Mol → PyG `Data` (FR‑002). 5. Exclude molecules missing `homo` or unparsable SMILES; log counts; if >5 % → “Data Quality Warning” (FR‑012). | FR‑001, FR‑002, FR‑012 | SC‑001 |
| **3 – Model Implementation** | 1. Implement CPU‑only 3‑layer GCN per `data-model.md` (FR‑003, FR‑021). 2. Record architecture in `models/mpnn.py` (single source of truth). 3. Optimizer: Adam lr = 0.001; loss: MSE. | FR‑003, FR‑021 | SC‑003 |
| **4 – Training & Runtime Guard** | 1. Train on the **training split** (batch ≤ 64, early stopping patience = 10, max‑epochs = 200). 2. Monitor peak RSS via `psutil`; abort if > 7 GB (FR‑013). 3. Enforce **hard 6‑hour wall‑clock limit**; on timeout save checkpoint, flag reduced power (FR‑008). | FR‑003, FR‑008, FR‑013 | SC‑003, SC‑005 |
| **5 – Baseline Construction** | 1. Compute ECFP4 (radius 2) → Ridge regression (baseline 1). 2. Run DFTB on the full dataset; if runtime **> 30 min**, **fallback to a stratified modest‑sized k‑molecule subset**. Stratification: joint binning on **molecular weight** (5 equal‑frequency bins) and **HOMO energy** (5 equal‑frequency bins); sample proportionally from each joint bin to preserve the overall distribution. This subset is then used for the residual‑correlation analysis (baseline 2) (FR‑006, FR‑015, FR‑023). | FR‑006, FR‑015, FR‑023 | — |
| **6 – Ablation Study (Retraining)** | 1. **Two CI sub‑jobs** (Job B‑1 & Job B‑2) each train **5** models: baseline and perturbed (zeroed bond features). 2. Use a **10 000‑molecule** training subset by default (meets FR‑018). 3. **Runtime guard**: quick profiling run estimates per‑run wall‑clock. If estimate > 4 h, **re‑estimate statistical power** for a **5 000‑molecule** subset using the formula  

\[
N = \left(\frac{Z_{1-\alpha/2}+Z_{\text{power}}}{\Delta/\sigma}\right)^{2}
\]

with σ≈0.3 eV, Δ=0.1 eV, α=0.05 → required N is on the order of several dozen participants.. Since 5 000 ≫ 71, power remains ≥ 0.8; the job proceeds. If a more conservative σ estimate ever yields power < 0.8, the job aborts with a “Power Insufficient” error. 4. Record MAE distribution for each run. 5. **Bootstrap** (1 000 samples) on per‑molecule absolute‑error differences for confidence intervals. 6. Paired t‑test with **Bonferroni correction** across all ablation configs (FR‑007). | FR‑005, FR‑007, FR‑017, FR‑018, FR‑020 | SC‑002, SC‑009 |
| **7 – Attribution Generation** | 1. Compute **Integrated Gradients** for a **random subset of 1 000 test molecules** (stratified by scaffold) (FR‑011). 2. **Validation**: atom‑level IG scores are correlated with Hammett σ constants **only for molecules that have experimentally measured σ values**. Molecules lacking σ are excluded; the script logs the count of included molecules. If fewer than **100** molecules possess σ constants, the correlation step is **skipped** and a limitation note is added to the final report, avoiding selection bias. When enough data are available, report Pearson ρ and p‑value (significance p < 0.05). 3. Store results per `model_output.schema.yaml`. | FR‑011 | — |
| **8 – Comprehensive Evaluation** | 1. Compute MAE, RMSE, $R^2$ on the **test set**. 2. **Pass/Fail**: if MAE ≥ 0.4 eV, record “Performance Failure” and halt further reporting (SC‑001). 3. Compare to fingerprint LR baseline (FR‑006). 4. Correlate absolute error with molecular weight & rotatable bonds (FR‑009, SC‑007). 5. Sensitivity sweep over thresholds {0.4,0.45,0.5,0.55,0.6} (FR‑010, SC‑008). 6. Flag OOD test molecules whose Bemis‑Murcko scaffold is unseen (FR‑019, SC‑011). 7. Compute Pearson ρ between GNN residuals and **DFTB** residuals (using the DFTB subset if full DFTB not feasible); require |ρ| ≤ 0.2 (FR‑015, FR‑023, SC‑010). 8. Report generalization gap (Test MAE – Train MAE) (FR‑016). | FR‑006‑FR‑023 | SC‑001‑SC‑012 |
| **9 – Reporting & Reproducibility** | 1. Assemble `results/` folder (metrics CSV, attribution JSON, ablation JSON, OOD report). 2. Run the **full pipeline** on a fresh runner to verify reproducibility (Principle I). 3. Log all checksums, random seeds, runtime stats, and pass/fail flags. | — | All principles reinforced |
| **10 – CI Job Orchestration (FR‑025)** | 1. **Job A – Data Ingestion & Validation** (Phase 0 + Phase 2). 2. **Job B – Main Model Training** (Phase 3 + Phase 4). 3. **Job C‑1 & C‑2 – Ablation Retraining** (Phase 6 split into two CI jobs, each ≤ 6 h). 4. **Job D – Baseline Construction & Evaluation** (Phase 5 + Phase 8). 5. **Job E – Attribution & Final Reporting** (Phase 7 + Phase 9). Each job respects the **6‑hour wall‑clock limit** and the **7 GB RAM ceiling**; checkpoints are persisted between jobs. | FR‑025 | — |

## Risk & Mitigation
| Situation | Mitigation |
|---|---|
| Missing `homo` values | Phase 2 aborts with clear error (FR‑020). |
| Proxy validation fails ($R^2 < 0.9$ or MAE > 0.4 eV) | Phase 0 aborts with “Construct Validity Failure” (FR‑024). |
| Training exceeds 6 h | Checkpoint saved; subsequent jobs continue; report reduced power (FR‑008). |
| DFTB runtime too long | Stratified 5 k subset ensures representative distribution (Phase 5). |
| Ablation under‑powered | Power re‑estimation before fallback guarantees ≥ 0.8 power; abort otherwise. |
| Attribution data missing | Skip σ‑correlation if < 100 molecules, log limitation (Phase 7). |
| >5 % molecules excluded | “Data Quality Warning” logged (FR‑012). |
| Test molecule with unseen scaffold | Flag in OOD report, note potential higher error (FR‑019). |

## Compute Feasibility Decision
- **CPU‑First**: All training uses `torch` on `device="cpu"`.  
- **Batch Size**: Start at 64; if OOM, reduce stepwise (48 → 32 → 16).  
- **Epochs**: Up to 200 with early stopping (patience = 10) **and** a hard cap of 100 epochs for ablation runs to guarantee completion within the 6‑hour job budget.  
- **Memory Monitoring**: `psutil` logs peak RSS; abort if > 7 GB (FR‑013).  
- **Timeout**: Hard 6‑hour wall‑clock limit per CI **job**; the pipeline is split into three separate jobs (Training, Ablation, Attribution) and the ablation job is further split into two sub‑jobs (Job B‑1, Job B‑2) to stay within limits.  

---

