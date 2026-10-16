# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md)  
**Input**: Feature specification from `/specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md`

## Summary
The project must (1) obtain a **public joint dataset** containing SMILES strings **and** experimental fluorescence quantum yield (FQY) values, (2) parse SMILES into graph representations with RDKit, (3) split the data using a scaffold‑based standard split (e.g., majority for training and smaller portions for validation and test) while guaranteeing disjoint scaffolds, (4) train a lightweight GNN (< 5 M parameters) and a linear‑regression baseline on ECFP4 fingerprints, (5) evaluate both models on the scaffold‑disjoint test set, (6) apply Integrated Gradients or SHAP to produce chemically interpretable substructure attributions, and (7) generate all required visualizations. All steps run on the free‑tier GitHub Actions CPU runner within the 6‑hour limit.

**IMPORTANT DATA NOTE** – No open, verifiable dataset that already pairs SMILES with experimental FQY values is available in the verified‑source list. Researchers must supply an **open joint file** (`data/raw/joint.parquet` or `data/raw/joint.csv`) that contains at least **200** matched molecules. The pipeline will abort with a clear error if this file is missing or contains fewer than 200 records. This requirement is mandated by the panel concern *data_resources-a388e36a* and ensures all downstream steps operate on verified data.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` (unit & integration) – each FR is covered by a dedicated test.  
- **Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (no GPU needed).  
- **Constraints**: < 5 M trainable parameters; all computation must fit within 7 GB RAM and 6 h wall‑clock.  
- **Scale/Scope**: Minimum **sufficient** matched molecules after deterministic join; if fewer are found the pipeline aborts with a clear error (see FR‑010 handling).  

## Constitution Check
| Principle | How the plan satisfies / references it |
|-----------|----------------------------------------|
| **I. Reproducibility** | Fixed random seeds (`numpy`, `torch`, `random`) are set in every script; dataset URLs are immutable; the entire pipeline is scripted from download to final report. |
| **II. Verified Accuracy** | All external URLs are taken from the verified list in `research.md`. No unverified source is introduced. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata; no in‑place modifications. |
| **IV. Single Source of Truth** | `results/metrics.json`, `figures/`, and `attributions/` are the sole sources for numbers and visualizations used in the paper. |
| **V. Versioning Discipline** | Artifacts (models, splits, attribution results) are saved with content‑hash filenames; any change updates the hash in `state/projects/...yaml`. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) is enforced; overlap statistics are logged (FR‑014) and verified to be zero (SC‑004). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients/SHAP produce ranked substructure lists (FR‑006) validated against an **independent** curated motif set (SC‑005). |

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
├── data/                # download scripts, raw files, checksum utils
├── preprocessing/       # deterministic join, clipping, scaffold split, metadata capture
├── features/            # node/edge feature extraction, ECFP4 fingerprint generation
├── models/              # GNN definition (<5 M params), linear‑regression baseline
├── training/            # training loop, early stopping, checkpointing
├── evaluation/          # metric computation, condition‑wise reporting
├── interpretability/    # Integrated Gradients / SHAP, substructure aggregation, reference‑set validation
└── utils/               # logging, seed handling, checksum verification
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks (maps to FR / SC) |
|-------|--------------------------|
| **0️⃣ Data Acquisition & Verification** | • Download the **user‑provided joint SMILES + FQY file** (`data/raw/joint.parquet` or `data/raw/joint.csv`). <br>• Verify checksum; abort if file missing or contains < 200 molecules (FR‑010, data‑resource concern). |
| **1️⃣ Deterministic Join & Pre‑processing** | • Generate InChIKey for each SMILES and ensure consistency (already part of joint file). <br>• Exclude invalid SMILES, log (FR‑009). <br>• Clip boundary FQY values to `[ε, 1‑ε]` with `ε = 1e‑6`, log occurrences (FR‑011). <br>• No additional scaling; `fqy_norm` = clipped values (FR‑010 update). <br>• Capture solvent/temperature/method metadata (FR‑015). <br>• Perform scaffold‑based 80/10/10 split (FR‑002, SC‑004). <br>• Log split counts & scaffold overlap (FR‑014). <br>• If the test set contains **fewer than 20 molecules**, log a warning but **do not alter** the split ratios (FR‑013). If the split cannot satisfy the ≥ 20 test‑molecule floor, fallback to **80/15/5** while preserving zero scaffold overlap. |
| **2️⃣ Feature Engineering** | • Extract node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation) (FR‑001). <br>• Compute ECFP4 fingerprints for the linear‑regression baseline (FR‑005). |
| **3️⃣ Model Definition** | • Implement lightweight GNN (< 5 M params) with PyTorch Geometric (FR‑003). <br>• Define linear regression on ECFP4 (FR‑005). |
| **4️⃣ Training** | • Train GNN ≤ 50 epochs, early stopping patience = 10 (FR‑004). <br>• Adam optimizer, MSE loss (FR‑004). <br>• Save checkpoint of best validation loss (FR‑004). |
| **5️⃣ Evaluation** | • Compute R², RMSE, MAE on scaffold‑disjoint test set for both models (FR‑005). <br>• Stratify metrics by solvent/temperature/method if metadata present (FR‑017). <br>• Log overall & condition‑specific metrics (SC‑001). |
| **6️⃣ Interpretability** | • Apply Integrated Gradients **or** SHAP to the trained GNN (FR‑006). <br>• Detect unseen atom/bond types during inference; log a warning and **skip** the molecule (FR‑012). <br>• Aggregate atom‑level attributions into contiguous aromatic or conjugated fragments (FR‑006). <br>• Rank the top substructures and save `AttributionResult`. |
| **7️⃣ Attribution Validation** | • **Reference‑Set Independence**: Curated fluorophore‑motif list (Supplementary Table S1) is assembled from external literature (URLs listed in the repo) **and** cross‑checked against every molecule in training and test splits; any overlapping entry is removed before validation (scientific‑soundness‑68e86578). <br>• **Overlap Check**: Compute how many of the top 20 substructures appear in the curated list; require **≥ 12** matches (≥ 60 %). <br>• **Random Baseline**: Sample 20 fragments **excluding any fragment present in the curated list** from the full dataset, repeat a sufficient number of times to build a null distribution; observed overlap must be **≥ 1.5 ×** the mean of this null distribution (SC‑005, scientific‑soundness‑67e7acba). <br>• **Spot‑check**: For the five highest‑FQY test molecules, require ≥ 3 of their top‑5 substructures to match the curated list (SC‑005). |
| **8️⃣ Visualization** | • Training convergence plot, parity plot, substructure importance bar chart (FR‑007). |
| **9️⃣ Resource Monitoring** | • Record total wall‑clock time (SC‑002). <br>• Record peak RAM usage (SC‑003). |
| **🔟 Reporting** | • Write `results/metrics.json`, `figures/`, `attributions/` adhering to `contracts/processed_dataset.schema.yaml`. <br>• All downstream paper artifacts trace back to these files (Principle IV). |

## Power‑Analysis & Minimum Test‑Set Size
- **Effect‑size justification**: Prior fluorescence‑quantum‑yield regression studies report typical test‑set R² values in a moderate‑to‑high range (e.g., *J. Chem. Inf. Model.*, 2023, 63, 12). We adopt a conservative target **R² ≥ 0.6** for power calculations.  
- **Sample‑size estimation**: With α = 0.05, power = 0.80, and an expected R² = 0.6, a Simple linear regression requires a modest number of test points sufficient for reliable estimation. Our scaffold split aims for **≥ 20** test molecules as a hard warning threshold; if the split yields fewer, a warning is logged (≥ 20); fallback to 80/15/5 split while preserving zero scaffold overlap.  
- **Fallback split**: If the strict 80/10/10 split cannot satisfy the ≥ 20 test‑molecule floor, we automatically adjust to **80/15/5** (train/val/test) while preserving zero scaffold overlap.

## Timeline (estimated on CI runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | 15 min |
| Join, clipping, scaffold split | 35 min |
| Feature generation (ECFP4) | 10 min |
| GNN training (≤ 50 epochs) | 2 h 30 min |
| Baseline training & evaluation | 20 min |
| Attribution & aggregation | 30 min |
| Attribution validation & random baseline | 20 min |
| Visualization & reporting | 15 min |
| **Total** | **~4 h 35 min** (well under the 6 h limit) |

---

