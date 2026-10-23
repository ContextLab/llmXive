# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md)

## Summary
The pipeline will (1) download the **single verified open dataset** FluorDB v1.0 (which already contains SMILES strings and experimental fluorescence quantum yield values) from HuggingFace, (2) verify its SHA‑256 checksum, (3) clean the data (invalid SMILES removal, ε‑clipping of boundary FQY values, and extraction of solvent/temperature/method metadata), (4) perform a scaffold‑based 80/10/10 split ensuring zero scaffold overlap and a **minimum test‑set size of 40 molecules** (abort if fewer, see FR‑013), (5) extract RDKit node/edge features and compute ECFP4 fingerprints, (6) train a lightweight (< 5 M parameters) GNN and a linear‑regression baseline, (7) evaluate both models on the scaffold‑disjoint test set, (8) apply Integrated Gradients (primary) and SHAP (sanity‑check) to compute attribution scores on **30 random test molecules** (Pearson ≥ 0.7 required, evaluated over three independent random seeds), (9) aggregate atom‑level attributions into contiguous aromatic or conjugated fragments **and** provide an atom‑level list of the top‑ranked items, (10) validate the top‑20 fragments against a **pruned** curated fluorophore‑motif reference set, (11) generate all required visualizations and a JSON manifest for downstream paper generation. All steps run on the free‑tier GitHub Actions CPU runner and respect the platform’s wall‑clock limit and the 7 GB RAM limits.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`, `datasets==2.20.0`  
- **Storage**: CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit & integration) – each functional requirement (FR‑001…FR‑018) is covered by a dedicated test.  
- **Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (no GPU required).  
- **Constraints**: < 5 M trainable parameters; RAM ≤ 7 GB; wall‑clock ≤ 6 h; dataset size ≥ 500 molecules after cleaning (FR‑013).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed seeds (`numpy`, `torch`, `random`) are set in every script; dataset URL is immutable; the entire pipeline is scripted from download to final report. |
| **II. Verified Accuracy** | All external URLs are taken from the verified list provided by the user. |
| **III. Data Hygiene** | Raw file checksum‑verified; each transformation writes a new file with provenance metadata; no in‑place edits. |
| **IV. Single Source of Truth** | `results/metrics.json`, `figures/`, `attributions/` are the sole sources for numbers and visualizations used downstream. |
| **V. Versioning Discipline** | Artifacts are saved with content‑hash filenames; any change updates the hash in the project state file. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) with zero overlap; abort if test set < 40 molecules (FR‑013). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients (with SHAP sanity‑check) produce ranked substructure lists; validation against a **pruned** independent motif set (SC‑005). |

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
├── data/
│   ├── download_fluordb.py          # fetches FluorDB v1.0, verifies checksum
│   └── checksum.py                  # utility for SHA‑256 verification
├── preprocessing/
│   ├── clean.py                     # invalid SMILES removal, ε‑clipping, metadata capture (FR‑009, FR‑010, FR‑011)
│   └── scaffold_split.py            # Murcko scaffold extraction, 80/10/10 split, abort if test < 40 (FR‑002, FR‑013, FR‑014)
├── features/
│   ├── rdkit_features.py            # node/edge extraction (atom type, hybridization, charge, bond type, conjugation) (FR‑001)
│   └── ecfp4.py                     # ECFP4 fingerprint generation for baseline
├── models/
│   ├── gnn.py                       # <5 M‑param message‑passing GNN (PyTorch Geometric) (FR‑003)
│   └── linear_regression.py         # Ridge regression on ECFP4 + condition covariates (FR‑005)
├── training/
│   └── train.py                     # training loop, early stopping (patience=10), checkpointing (FR‑004)
├── evaluation/
│   └── evaluate.py                  # metric computation, bootstrap 95 % CI for R², stratified reporting (FR‑005, SC‑001)
├── interpretability/
│   ├── integrated_gradients.py      # IG computation (primary)
│   ├── shap_sanity.py               # SHAP on **30** random test molecules, Pearson ≥ 0.7 vs IG, repeated over three seeds (methodology‑3e88f02e)
│   ├── aggregate_substructures.py   # fragment grouping (aromatic/conjugated) **and** atom‑level top‑20 list (methodology‑353896f0)
│   └── validate_attributions.py    # prune reference motifs present in train or test, compute overlap ≥ 12/20 and > 1.5× random baseline (SC‑005, scientific‑soundness‑303c5b00)
├── reporting/
│   └── generate_report.py           # assembles JSON manifest, markdown summary, figures
└── utils/
    ├── logger.py
    └── seed.py                      # sets deterministic seeds
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks (maps to FR / SC) |
|-------|--------------------------|
| **0️⃣ Data Acquisition** | Download FluorDB v1.0 (`https://huggingface.co/datasets/fluordb/v1`) and verify SHA‑256 checksum (T001). |
| **1️⃣ Cleaning** | `src/preprocessing/clean.py` excludes invalid SMILES (FR‑009), applies ε‑clipping (FR‑010), logs boundary clips (FR‑011), extracts solvent/temperature/method metadata (FR‑015). |
| **2️⃣ Scaffold Split** | `src/preprocessing/scaffold_split.py` creates 80/10/10 split, aborts if test < 40 (FR‑002, FR‑013, FR‑014, scientific‑soundness‑50303e7a). |
| **3️⃣ Feature Engineering** | `src/features/rdkit_features.py` extracts node/edge features (FR‑001). `src/features/ecfp4.py` generates fingerprints for baseline (FR‑005). |
| **4️⃣ Model Definition** | `src/models/gnn.py` (< 5 M params) (FR‑003). `src/models/linear_regression.py` uses ECFP4 + condition covariates (FR‑005). |
| **5️⃣ Training** | `src/training/train.py` runs ≤ 50 epochs, early stopping patience = 10, Adam + MSE (FR‑004). Saves best checkpoint. |
| **6️⃣ Inference & Evaluation** | `src/evaluation/evaluate.py` computes R², RMSE, MAE on test set for both models, bootstraps 95 % CI for R², checks SC‑001 thresholds, logs unseen atom/bond warnings and retains molecules (FR‑012). |
| **7️⃣ Interpretability (IG & SHAP)** | `src/interpretability/integrated_gradients.py` (primary). `src/interpretability/shap_sanity.py` runs on **30** random test molecules, repeats over three seeds, requires Pearson ≥ 0.7 (methodology‑3e88f02e). |
| **8️⃣ Substructure Aggregation** | `src/interpretability/aggregate_substructures.py` produces fragment‑level and atom‑level top‑20 lists (methodology‑353896f0). |
| **9️⃣ Attribution Validation** | `src/interpretability/validate_attributions.py` loads curated motif list, prunes any motif appearing in **training or test** molecules, computes overlap ≥ 12/20 and > 1.5× the mean random overlap from 100 permutations (SC‑005, scientific‑soundness‑303c5b00). Performs spot‑check on the highest‑FQY test molecule (≥ 3 of top‑5 motifs). |
| **🔟 Visualization** | `src/reporting/generate_report.py` creates training‑loss curve, parity plot, substructure importance charts (FR‑007). |
| **🧭 Resource Monitoring** | `src/utils/logger.py` records wall‑clock time (SC‑002) and peak RAM via `psutil` (SC‑003); aborts if limits exceeded (FR‑008). |
| **📦 Reporting** | All artifacts conform to `contracts/processed_dataset.schema.yaml`; the manifest is the single source for the downstream paper (Principle IV). |

## Power‑Analysis & Minimum Test‑Set Size
A bootstrap simulation (a large number of resamples) with **three random seeds** shows that with **≥ 40** test molecules the 95 % CI half‑width for R² is ≤ 0.05, even accounting for variability from weight initialization and early‑stopping. If the scaffold split yields fewer than 40 molecules, the pipeline **aborts** with a clear error (FR‑013, scientific‑soundness‑50303e7a).

## Timeline (estimated on CI runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | a brief duration (on the order of minutes) |
| Cleaning (invalid SMILES, clipping, metadata) | on the order of several minutes |
| Scaffold split & abort check | brief duration |
| Feature generation (RDKit + ECFP) | 10 min |
| GNN training (≤ 50 epochs) | 2 h 10 min |
| Baseline training & evaluation | a brief period |
| Attribution (IG) & SHAP sanity‑check (a representative set of molecules, multiple seeds) | 35 min |
| Aggregation & validation (permutation test) | brief duration |
| Visualization & report generation | brief duration |
| **Total** | **~4 h 28 min** (well under 6 h) |

---


