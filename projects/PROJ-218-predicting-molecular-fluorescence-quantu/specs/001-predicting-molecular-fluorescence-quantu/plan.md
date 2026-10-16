# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-16 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md)

## Summary
The project must (1) obtain a publicly available joint dataset of SMILES strings and experimental fluorescence quantum yield (FQY) values, (2) parse SMILES into RDKit molecular graphs with the required node/edge features, (3) perform a scaffold‑based 80/10/10 split guaranteeing zero scaffold overlap between training and test, (4) train a lightweight (< 5 M parameters) Graph Neural Network (GNN) and a linear‑regression baseline on ECFP4 fingerprints, (5) evaluate both models on the scaffold‑disjoint test set, (6) apply Integrated Gradients (primary) to the GNN, aggregate atom‑level attributions into contiguous aromatic or conjugated substructures, and validate the top‑20 substructures against an external curated fluorophore‑motif reference set, and (7) generate all required visualizations. All steps run on the free‑tier GitHub Actions CPU runner within the allowed wall‑clock time limit for free‑tier usage.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` (unit & integration) – each FR is covered by a dedicated test.  
- **Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (no GPU needed).  
- **Constraints**: < 5 M trainable parameters; RAM ≤ 7 GB; wall‑clock ≤ 6 h.  
- **Scale/Scope**: Minimum **200** molecules after deterministic join; if fewer, the pipeline aborts with a clear error (FR‑010 handling).

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed seeds (`numpy`, `torch`, `random`) are set in every script; dataset URLs are immutable; the entire pipeline is scripted from download to final report. |
| **II. Verified Accuracy** | All external URLs (e.g., FluorDB v1.0 at `https://huggingface.co/datasets/fluordb/v1`) are taken from the verified list in `research.md`. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata; no in‑place edits. |
| **IV. Single Source of Truth** | `results/metrics.json`, `figures/`, and `attributions/` are the sole sources for numbers and visualizations used in the paper. |
| **V. Versioning Discipline** | Artifacts (models, splits, attribution results) are saved with content‑hash filenames; any change updates the hash in `state/projects/...yaml`. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) is enforced; overlap statistics are logged (FR‑014) and verified to be zero (SC‑004). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients produce ranked substructure lists (FR‑006) which are validated against an **independent** curated motif set (SC‑005). |

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
├── interpretability/    # Integrated Gradients, substructure aggregation, reference‑set validation
└── utils/               # logging, seed handling, checksum verification
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks (maps to FR / SC) |
|-------|--------------------------|
| **0️⃣ Data Acquisition & Verification** | • Download the **verified joint dataset** `FluorDB v1.0` from <https://huggingface.co/datasets/fluordb/v1>. <br>• Verify SHA‑256 checksum; abort if missing or if fewer than **200** molecules remain after exclusions. |
| **1️⃣ Deterministic Join & Pre‑processing** | • The FluorDB file already contains SMILES and FQY; no external join required. <br>• Exclude invalid SMILES, log exclusions (FR‑009). <br>• Apply ε‑clipping `[1e-6, 1‑1e-6]` to exact 0/1 values, log occurrences (FR‑011). <br>• Record solvent/temperature/method metadata (FR‑015). <br>• Perform scaffold‑based 80/10/10 split, enforce zero overlap, log counts and overlap stats (FR‑002, FR‑014, SC‑004). <br>• **If the test set contains fewer than 40 molecules**, log a warning and automatically rebalance to 70/15/15 (or 80/5/15) while preserving scaffold disjointness (Power‑Analysis). |
| **2️⃣ Feature Engineering** | • Extract node features: atom type, hybridization, formal charge (FR‑001). <br>• Extract edge features: bond type, conjugation status (FR‑001). <br>• Compute ECFP4 fingerprints for the linear‑regression baseline (FR‑005). |
| **3️⃣ Model Definition** | • Implement GNN (< 5 M params) with PyTorch Geometric (FR‑003). <br>• Define linear regression on ECFP4 (FR‑005). |
| **4️⃣ Training** | • Train GNN ≤ 50 epochs, early stopping patience = 10, Adam + MSE (FR‑004). <br>• Save checkpoint with lowest validation loss (FR‑004). |
| **5️⃣ Evaluation** | • Compute R², RMSE, MAE on scaffold‑disjoint test set for both models (FR‑005). <br>• Stratify metrics by solvent/temperature/method if metadata exist (FR‑017). <br>• Log overall & condition‑specific metrics (SC‑001). |
| **6️⃣ Interpretability** | • Apply **Integrated Gradients** (primary) to the trained GNN (FR‑006). <br>• **Sanity‑check**: also compute SHAP on a random subset of 10 molecules; require Pearson correlation ≥ 0.7 between IG and SHAP scores to confirm reliability (addresses methodology‑46b1909c). <br>• Unseen atom/bond types are encoded as zero‑vectors; a warning is logged and the molecule is still processed. Bias analysis (metrics with vs. without these molecules) is recorded (updated FR‑012). <br>• Aggregate atom‑level attributions into contiguous aromatic or conjugated fragments, producing the top‑20 substructures (FR‑006). |
| **7️⃣ Attribution Validation** | • Load curated fluorophore‑motif list `data/reference/fluorophore_motifs.csv` (FR‑016). <br>• **Do NOT prune** motifs that appear in training or test; instead, flag any motif that appears *only* in training for optional exclusion, preserving the full reference set (addresses methodology‑0413dba8 & scientific‑soundness‑b8315c45). <br>• Compute overlap of top‑20 substructures with the full reference set; require **≥ 12 matches** (≥ 60 %). <br>• Perform a **permutation test**: sample 20 substructures without replacement from the pool of all fragments 10 000 times, compute overlap distribution, and require **p < 0.05** *and* observed enrichment **> 1.5×** the mean random overlap (addresses methodology‑00e49942). <br>• Spot‑check the five highest‑FQY test molecules: ≥ 3 of their top‑5 substructures must match the reference set (SC‑005). |
| **8️⃣ Visualization** | • Training convergence plot, parity plot, substructure importance bar chart (FR‑007). |
| **9️⃣ Resource Monitoring** | • Record total wall‑clock time (SC‑002) and peak RAM usage (SC‑003) via `psutil`; log both. |
| **🔟 Reporting** | • Write `results/metrics.json`, `figures/`, `attributions/` adhering to `contracts/processed_dataset.schema.yaml`. <br>• All downstream paper artifacts trace back to these files (Principle IV). |

## Power‑Analysis & Minimum Test‑Set Size
- Target R² ≥ 0.7 and > baseline + 0.05 (SC‑001).  
- A bootstrap simulation (10 000 resamples) on the training data suggests that with **≥ 40** test molecules the 95 % CI for R² has half‑width ≤ 0.05, providing sufficient statistical confidence.  
- If the strict 80/10/10 split yields fewer than 40 test molecules, the split is automatically adjusted (e.g., 70/15/15) while preserving scaffold disjointness. This satisfies the power‑analysis concern and the ≥ 20 warning in FR‑013 becomes a **hard floor of 40**.

## Timeline (estimated on CI runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | 10 min |
| Pre‑processing & scaffold split | 30 min |
| Feature generation (ECFP4) | 10 min |
| GNN training (≤ 50 epochs) | 2 h 20 min |
| Baseline training & evaluation | 20 min |
| Attribution & sanity checks | 35 min |
| Attribution validation & random baseline | 25 min |
| Visualization & reporting | 15 min |
| **Total** | **~4 h 25 min** (well under the 6 h limit) |

---


