# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-14 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantum-yields/spec.md)

## Summary
The project must ingest a public molecular dataset containing SMILES strings and experimental fluorescence quantum yield (FQY) values, convert SMILES to graph representations, split the data using a scaffold‑based strategy, train a lightweight GNN, compare it against an ECFP4 linear‑regression baseline, and provide substructure‑level interpretability via Integrated Gradients or SHAP. All steps must run on the free‑tier GitHub Actions CPU runner within the 6‑hour limit.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`  
- **Storage**: File‑based CSV/Parquet in `data/`  
- **Testing**: `pytest` (unit & integration) – tests will validate each FR independently.  
- **Target Platform**: Linux (GitHub Actions runner) – CPU‑only.  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 7 GB.  
- **Constraints**: < 5 M trainable parameters, no GPU usage (CPU‑first).  
- **Scale/Scope**: Minimum 500 molecules (as assumed by the spec).  

## Constitution Check
| Principle | How the plan satisfies / references it |
|-----------|----------------------------------------|
| **I. Reproducibility** | All random seeds are fixed in scripts; dataset URLs are immutable; the pipeline is fully scripted. |
| **II. Verified Accuracy** | All external citations will be limited to the verified URLs listed in the “Verified datasets” block. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata. |
| **IV. Single Source of Truth** | `results/metrics.json` and all files under `figures/` are designated as the authoritative source for reported numbers and visualizations. |
| **V. Versioning Discipline** | Artifacts (models, splits, attribution results) are saved with content‑hash filenames. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) is enforced; overlap statistics are logged (FR‑014). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients/SHAP produce ranked substructure lists (FR‑006, SC‑005). |

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
├── data/                # download scripts, raw files, checksums
├── preprocessing/       # SMILES → graph, scaffold split, normalization, metadata capture, join validation
├── models/              # GNN definition, baseline model
├── training/            # training loop, early stopping, checkpointing
├── evaluation/          # metric computation, condition‑wise reporting
├── interpretability/    # Integrated Gradients / SHAP, substructure aggregation, reference‑set independence check
└── utils/               # logging, seed handling, checksum utils
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | Tasks (maps to FR / SC) |
|-------|--------------------------|
| **0️⃣ Data Acquisition & Verification** | • Download verified SMILES parquet file (FR‑001). <br>• Download verified FQY JSON file (FR‑001). <br>• Verify checksums (Principle III). |
| **1️⃣ Data Curation & Pre‑processing** | • Parse SMILES with RDKit → `MoleculeGraph` (FR‑001). <br>• **Join Validation**: generate InChI from each SMILES, match to FQY entries by InChI; require ≥ 200 matched molecules, otherwise abort with clear error (addresses data‑gap concerns). <br>• Exclude invalid SMILES, log (FR‑009). <br>• Clip boundary FQY values, log (FR‑010, FR‑011). <br>• Capture solvent, temperature, measurement‑method metadata into `metadata` column (FR‑015). <br>• Compute min‑max scaling on training set only (FR‑010). <br>• Scaffold‑based split (80/10/10) (FR‑002, SC‑004). <br>• Log split counts & overlap (FR‑014). <br>• Warn if test set < 20 molecules (FR‑013). |
| **2️⃣ Feature Engineering** | • Generate node/edge features (atom type, hybridization, formal charge, bond type, conjugation) (FR‑001). <br>• Compute ECFP4 fingerprints for baseline (FR‑005). |
| **3️⃣ Model Definition** | • Implement lightweight GNN (< 5 M params) with PyTorch Geometric (FR‑003). <br>• Define linear regression baseline on ECFP4 (FR‑005). |
| **4️⃣ Training** | • Train GNN for ≤ 50 epochs, early stopping patience = 10 (FR‑004). <br>• Use Adam optimizer, MSE loss (FR‑004). <br>• Save checkpoint of best validation loss (FR‑004). |
| **5️⃣ Evaluation** | • Compute R², RMSE, MAE on held‑out test set for both models (FR‑005). <br>• Stratify metrics by solvent/temperature/method if metadata present (FR‑017). <br>• Log overall & condition‑specific metrics (SC‑001). |
| **6️⃣ Interpretability** | • Apply Integrated Gradients **or** SHAP to trained GNN (FR‑006). <br>• **Unseen Atom/Bond Handling (FR‑012)**: during inference, detect atom/bond types absent from training set, log warning, and skip the molecule; retain for evaluation with a summary report. <br>• Aggregate atom attributions into contiguous aromatic or conjugated substructures (FR‑006). <br>• Rank the top substructures., save `AttributionResult` (FR‑006). |
| **7️⃣ Validation of Attribution** | • **Reference‑Set Independence Check**: verify that the curated fluorophore‑motif list (Supplementary Table S1) contains no molecules from the training or test sets; log any overlap (addresses scientific soundness‑78b9e565). <br>• Compute overlap with reference set (≥ 12 of 20 matches) and enrichment > 1.5× random baseline (SC‑005). <br>• Random‑Baseline Definition: sample 20 unique SMARTS fragments uniformly from the full pool of fragments (excluding the top‑20), repeat 100 times to build null distribution (addresses scientific soundness‑38c39e69). <br>• Spot‑check top‑5 high‑FQY molecules for ≥ 3 matching motifs (SC‑005). |
| **8️⃣ Visualization** | • Training convergence plot (FR‑007). <br>• Parity plot (predicted vs experimental) (FR‑007). <br>• Bar chart of substructure importance (FR‑007). |
| **9️⃣ Resource Monitoring** | • Record total wall‑clock time (SC‑002). <br>• Record peak RAM usage (SC‑003). |
| **🔟 Reporting & Artifact Generation** | • Write `results/metrics.json`, `figures/`, `attributions/` adhering to `contracts/processed_dataset.schema.yaml`. <br>• All downstream paper‑stage artifacts will trace back to these files (Single Source of Truth). |

## Data Gap & Scope Adjustment
*The verified dataset list does **not** contain a single source that provides both SMILES strings **and** experimental FQY values.*  

**Resolution Strategy**
1. **Deterministic Join** – Convert each SMILES to an InChI key (`rdkit.Chem.inchi.MolToInchiKey`). Match records from the SMILES parquet and the FQY JSON on this key.  
2. **Validation** – After joining, require **≥ 200** matched molecules ([deferred] of the assumed minimum). If fewer matches are obtained, the pipeline aborts with a clear error message directing the researcher to supply an open joint dataset.
3. **Fallback** – No synthetic stand‑in is used. The project owner must either (a) provide an open dataset that already contains both fields (e.g., a curated FluorDB release) or (b) accept that the analysis cannot proceed under the current data constraints.

## Power‑Analysis & Minimum Test‑Set Size
Using a two‑sided α = 0.05, desired power = 0.80, and an anticipated effect size corresponding to R² = 0.7 (Cohen’s f² ≈ 2.33), a **minimum total sample size of a sufficient magnitude** is required; with an 80/10/10 scaffold split this yields **≈ 26** test molecules. To ensure robust estimation and to satisfy SC‑001, we set a **conservative minimum test‑set size of a sufficiently large number of molecules**. If the scaffold split yields fewer than 70 test molecules, a warning is logged (FR‑013) and SC‑001 is treated as exploratory.

## Timeline (estimated on CI runner)
| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | 15 min |
| Join validation & preprocessing | 35 min |
| Feature generation (ECFP4) | 10 min |
| GNN training (≤ 50 epochs) | 2 h 30 min |
| Baseline training & evaluation | 20 min |
| Attribution & aggregation | 30 min |
| Attribution validation & random baseline | 20 min |
| Visualization & reporting | 15 min |
| **Total** | **~4 h 35 min** (well under the 6 h limit) |

---

