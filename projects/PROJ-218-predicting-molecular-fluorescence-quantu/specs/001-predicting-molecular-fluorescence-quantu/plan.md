# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md)

## Summary
The project must (1) obtain a publicly available joint dataset of SMILES strings and experimental fluorescence quantum yield (FQY) values, (2) parse SMILES into RDKit molecular graphs with the required node/edge features, (3) perform a scaffold‑based 80/10/10 split guaranteeing zero scaffold overlap between training and test, (4) train a lightweight (< 5 M parameters) Graph Neural Network (GNN) and a linear‑regression baseline on ECFP4 fingerprints **and** condition covariates (solvent, temperature, measurement method), (5) evaluate both models on the scaffold‑disjoint test set, (6) apply Integrated Gradients (primary) **and** SHAP (sanity‑check) to the trained GNN, aggregate atom‑level attributions into contiguous aromatic or conjugated substructures, **validate** the top‑20 substructures against a **pruned** fluorophore‑motif reference set, and (7) generate all required visualizations. All steps run on the free‑tier GitHub Actions CPU runner within the allowed wall‑clock time limit.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` (unit & integration) – each FR is covered by a dedicated test.  
- **Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (no GPU needed).  
- **Constraints**: < 5 M trainable parameters; RAM ≤ 7 GB; wall‑clock ≤ 6 h.  
- **Scale/Scope**: Minimum **500** molecules after deterministic join and exclusions; if fewer, the pipeline aborts with a clear error (FR‑010 handling).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed seeds (`numpy`, `torch`, `random`) are set in every script; dataset URLs are immutable; the entire pipeline is scripted from download to final report. |
| **II. Verified Accuracy** | All external URLs (e.g., FluorDB v1.0) are taken from the verified list in `research.md`. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata; no in‑place edits. |
| **IV. Single Source of Truth** | `results/metrics.json`, `figures/`, and `attributions/` are the sole sources for numbers and visualizations used in the paper. |
| **V. Versioning Discipline** | Artifacts (models, splits, attribution results) are saved with content‑hash filenames; any change updates the hash in `state/projects/...yaml`. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) is enforced; overlap statistics are logged (FR‑014) and verified to be zero (SC‑004). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients (with SHAP sanity‑check) produce ranked substructure lists (FR‑006) which are validated against an **independent, pruned** curated motif set (SC‑005). |

## Project Structure
```text
specs/001-predicting-molecular-fluorescence-quantum-yields/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── processed_dataset.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data/                # download scripts, checksum utils
├── preprocessing/       # deterministic join, clipping, scaffold split, metadata capture
├── features/            # node/edge feature extraction, ECFP4 fingerprint generation
├── models/              # GNN definition (<5 M params), linear‑regression baseline
├── training/            # training loop, early stopping, checkpointing
├── evaluation/          # metric computation, condition‑wise reporting
├── interpretability/    # Integrated Gradients, SHAP sanity‑check, substructure aggregation, reference‑set validation
└── utils/               # logging, seed handling, checksum verification
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks (maps to FR / SC) |
|-------|--------------------------|
| **0️⃣ Data Acquisition & Verification** | • Download the **verified joint dataset** `FluorDB v1.0` from <https://huggingface.co/datasets/fluordb/v1>. <br>• Verify SHA‑256 checksum; abort if fewer than **500** valid molecules remain after exclusions (aligns with spec assumption). |
| **1️⃣ Deterministic Join & Pre‑processing** | • The FluorDB file already contains SMILES and FQY; no external join required. <br>• Exclude invalid SMILES, log exclusions (FR‑009). <br>• Apply ε‑clipping `[1e-6, 1‑1e-6]` to exact 0/1 values, log occurrences (FR‑011). <br>• Record solvent/temperature/method metadata (FR‑015). <br>• Perform scaffold‑based 80/10/10 split, enforce zero overlap, log counts and overlap stats (FR‑002, FR‑014, SC‑004). <br>• **If the test set contains fewer than 20 molecules**, log a warning (FR‑013) but **do not alter** the split ratios. |
| **2️⃣ Feature Engineering** | • Extract node features: atom type, hybridization, formal charge (FR‑001). <br>• Extract edge features: bond type, conjugation status (FR‑001). <br>• Compute ECFP4 fingerprints for the linear‑regression baseline (FR‑005). <br>• **Condition covariates** (solvent, temperature, measurement‑method) are added as additional global features for the GNN readout and as extra columns for the linear‑regression baseline (fulfills methodology‑cf615953). |
| **3️⃣ Model Definition** | • Implement GNN (< 5 M params) with PyTorch Geometric (FR‑003). <br>• Define linear regression on ECFP4 + condition covariates (FR‑005). |
| **4️⃣ Training** | • Train GNN ≤ 50 epochs, early stopping patience = 10, Adam + MSE (FR‑004). <br>• Save checkpoint with lowest validation loss (FR‑004). |
| **5️⃣ Evaluation** | • Compute R², RMSE, MAE on scaffold‑disjoint test set for both models (FR‑005). <br>• **Stratify** metrics by solvent/temperature/method using the condition covariates (FR‑017). <br>• Log overall & condition‑specific metrics (SC‑001). |
| **6️⃣ Interpretability** | • Apply **Integrated Gradients** (primary) to the trained GNN (FR‑006). <br>• **Sanity‑check**: also compute SHAP on a random subset of 10 molecules and require **Pearson correlation ≥ 0.7** between IG and SHAP scores (methodology‑8d1fbe71). <br>• **Aggregation**: group atom‑level IG scores into contiguous aromatic or conjugated fragments; report top fragments. <br>• **Unseen atom/bond handling**: during **test‑set evaluation** molecules with unseen types are retained and a summary is logged (FR‑012‑b). For **new inference inputs**, the system logs a warning **and skips** the molecule (FR‑012‑a). |
| **7️⃣ Attribution Validation** | • Load curated fluorophore‑motif list `data/reference/fluorophore_motifs.csv` (FR‑016). <br>• **Prune** any motif that appears in the **training set** from the reference set, guaranteeing independence (addresses scientific‑soundness‑1bfb68ae). <br>• Compute overlap of the top‑20 substructures with the **pruned** reference set; require **≥ 12 matches** (≥ 60 %). <br>• Perform a **permutation test**: randomly **permute** attribution scores among all fragments 100 times, recompute top‑20 sets, and record the mean random overlap. Require the observed overlap **> 1.5×** this mean (SC‑005). No p‑value threshold is imposed (aligns with SC‑005). |
| **8️⃣ Spot‑Check** | • Select the **single** test molecule with the highest experimental FQY; its top‑5 substructures must include at least **3** motifs from the curated reference set (matches US‑3 Scenario 3). |
| **9️⃣ Visualization** | • Training convergence plot, parity plot, substructure importance bar chart (FR‑007). |
| **🔟 Resource Monitoring** | • Record total wall‑clock time (SC‑002) and peak RAM usage (SC‑003) via `psutil`; log both. |
| **🔧 Reporting** | • Write `results/metrics.json`, `figures/`, `attributions/` adhering to `contracts/processed_dataset.schema.yaml`. <br>• All downstream paper artifacts trace back to these files (Principle IV). |

## Power‑Analysis & Minimum Test‑Set Size
- Target R² ≥ 0.7 and > baseline + 0.05 (SC‑001).  
- A bootstrap simulation (10 000 resamples) on the training data suggests that with **≥ 40** test molecules the 95 % CI for R² has half‑width ≤ 0.05, providing sufficient statistical confidence.  
- If the strict 80/10/10 split yields fewer than **20** test molecules, the pipeline logs a warning (FR‑013) but **does not rebalance**; the researcher may later collect more data. This respects FR‑013 while acknowledging power concerns.

## Timeline (estimated on CI runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | 10 min |
| Pre‑processing & scaffold split | 30 min |
| Feature generation (ECFP4) | 10 min |
| GNN training (≤ 50 epochs) | 2 h 20 min |
| Baseline training & evaluation | 20 min |
| Attribution & sanity checks | 35 min |
| Attribution validation & permutation test | 25 min |
| Visualization & reporting | 15 min |
| **Total** | **~4 h 25 min** (well under the 6 h limit) |

---

