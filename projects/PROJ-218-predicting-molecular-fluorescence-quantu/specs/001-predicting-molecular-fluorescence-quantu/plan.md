# Implementation Plan: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Branch**: `001-predicting-molecular-fluorescence-quantum-yields` | **Date**: 2026-10-22 | **Spec**: [spec.md](../specs/001-predicting-molecular-fluorescence-quantu/spec.md)

## Summary
The pipeline is designed to (1) ingest a **joint SMILES + experimental fluorescence quantum yield (FQY)** dataset from FluorDB v1.0, (2) clean and split the data using a scaffold‑based high‑proportion/10/10 strategy (with a **minimum of 50 test molecules**), (3) generate RDKit graph features and ECFP4 fingerprints, (4) train a lightweight (< 5 M parameters) GNN and a linear‑regression baseline, (5) evaluate both models on a scaffold‑disjoint test set, (6) compute Integrated Gradients (IG) and SHAP attributions on **100** random test molecules (three seeds) and report Pearson correlation with 95 % confidence intervals, (7) aggregate atom‑level attributions into chemically meaningful substructures, (8) validate the top‑N substructures against a **full** curated fluorophore‑motif reference set using a hypergeometric enrichment test (reporting p‑value and enrichment factor), (9) perform a covariate impact analysis, and (10) produce all required visualizations and a single JSON manifest for downstream paper generation.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torch_geometric==2.5.3`, `rdkit==2024.03.2`, `pandas==2.2.2`, `scikit-learn==1.5.0`, `shap==0.45.0`, `matplotlib==3.9.0`, `numpy==2.0.0`, `tqdm==4.66.5`, `datasets==2.20.0`  
- **Target Platform**: Linux (GitHub Actions free‑tier runner) – **CPU‑only** (no GPU required).  
- **Constraints**: ≤ 5 M trainable parameters, ≤ 7 GB RAM, ≤ 6 h wall‑clock time, dataset size after cleaning ≥ 500 rows (as assumed by the spec).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | Fixed random seeds are set in a shared `seed.py` module; the entire pipeline is scripted from download to final report; dataset URL is immutable. |
| **II. Verified Accuracy** | Uses the FluorDB v1.0 dataset as specified in the functional requirements (FR-018) and verifies data integrity via SHA-256 checksums. |
| **III. Data Hygiene** | Raw files are checksum‑verified; each transformation writes a new file with provenance metadata; no in‑place edits. |
| **IV. Single Source of Truth** | All quantitative results are stored in `results/metrics.json`, `results/attribution_validation.json`, and figures are generated from these files only. |
| **V. Versioning Discipline** | Artifacts are saved with content‑hash filenames; any change updates the hash in the project state file. |
| **VI. Scaffold‑Based Generalizability** | Scaffold split (80/10/10) with zero scaffold overlap; abort if test set < 50 molecules (FR‑013). |
| **VII. Explicit Substructure Attribution** | Integrated Gradients (primary) and SHAP (sanity‑check) produce ranked substructure lists; validation uses a hypergeometric test against the full curated motif set (SC‑005). |

## Project Structure
```text
specs/001-predicting-molecular-fluorescence-quanti/
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
│   ├── download_fluordb.py          # fetches FluorDB and verifies checksum
│   └── checksum.py                  # SHA‑256 verification utility
├── preprocessing/
│   ├── clean.py                     # invalid SMILES removal, ε‑clipping, metadata capture
│   └── scaffold_split.py            # Murcko scaffold extraction, 80/10/10 split, min‑test‑size = 50, reseed loop
├── features/
│   ├── rdkit_features.py            # node/edge extraction (atom type, hybridization, charge, bond type, conjugation)
│   └── ecfp4.py                     # ECFP4 generation for baseline
├── models/
│   ├── gnn.py                       # <5 M‑param message‑passing GNN (PyTorch Geometric)
│   └── linear_regression.py         # Ridge regression on ECFP4 + covariates
├── training/
│   └── train.py                     # ≤ 50 epochs, early stopping (patience = 10), checkpointing
├── evaluation/
│   ├── evaluate.py                  # R², RMSE, MAE on test set; bootstrap 95 % CI; logging of unseen atom/bond warnings
│   └── covariate_ablation.py        # train/evaluate with and without covariates, compare performance
├── interpretability/
│   ├── integrated_gradients.py      # IG computation (primary)
│   ├── shap_sanity.py               # SHAP on A random selection of test molecules., three seeds; Pearson ± 95 % CI
│   ├── aggregate_substructures.py   # fragment grouping (aromatic, conjugated) and top‑20 ranking
│   └── validate_attributions.py    # hypergeometric enrichment test vs full reference set; reports p‑value, enrichment factor
├── reporting/
│   └── generate_report.py           # assembles figures, tables, and JSON manifest
└── utils/
    ├── logger.py
    └── seed.py                      # sets deterministic seeds
tests/
├── unit/
├── integration/
└── contract/
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC) to Phases
| Phase | Tasks (FR) | Success Checks (SC) |
|-------|------------|---------------------|
| **0️⃣ Data Acquisition** | `download_fluordb.py` (FR‑018) – fetches the joint dataset and verifies checksum. | Logs success; verifies dataset presence. |
| **1️⃣ Cleaning** | `clean.py` – removes invalid SMILES (FR‑009), ε‑clips boundary FQY values (FR‑010), logs clips (FR‑011), extracts optional solvent/temperature/method metadata (FR‑015). | Generates `processed_dataset.schema.yaml`‑compliant parquet; logs counts. |
| **2️⃣ Scaffold Split** | `scaffold_split.py` – Murcko scaffold extraction, 80/10/10 split, ensures zero overlap (FR‑002, FR‑014), **minimum test size 50** (FR‑013). If test < 50, reseeds up to 5 attempts; aborts with warning if still insufficient. | Writes split statistics; SC‑004 verified. |
| **3️⃣ Feature Engineering** | `rdkit_features.py` (FR‑001); `ecfp4.py` (baseline). | Output files validated against schema. |
| **4️⃣ Model Definition** | `gnn.py` (FR‑003); `linear_regression.py` (FR‑005). | Parameter count < 5 M confirmed. |
| **5️⃣ Training** | `train.py` – ≤ 50 epochs, early stopping (patience = 10) (FR‑004). | Best checkpoint saved; training‑loss curve generated (FR‑007). |
| **6️⃣ Evaluation** | `evaluate.py` – compute R², RMSE, MAE (FR‑005); bootstrap 95 % CI for R²; log unseen atom/bond warnings (FR‑012). | Metrics written to `results/metrics.json`; SC‑001 reported (no hard thresholds). |
| **7️⃣ Interpretability (IG & SHAP)** | `integrated_gradients.py` (primary) (FR‑006); `shap_sanity.py` – **100** random test molecules, three seeds, Pearson ≥ 0.7 with 95 % CI (methodology‑3e88f02e). | If Pearson < 0.7 the pipeline **does not abort**; the metric is recorded for diagnostic purposes (SC‑006). |
| **8️⃣ Substructure Aggregation** | `aggregate_substructures.py` – produce top‑ranked fragment list (FR‑006). | Output JSON files. |
| **9️⃣ Attribution Validation** | `validate_attributions.py` – **no pruning** of the reference set; compute overlap count, enrichment factor, and hypergeometric p‑value against 100 random draws; spot‑check highest‑FQY molecule (SC‑005). | Validation JSON written; reports both overlap count, enrichment, and p‑value. |
| **🔟 Covariate Impact Analysis** | `covariate_ablation.py` – train/evaluate GNN and baseline **with** and **without** solvent/temperature/method covariates; compare R², RMSE, MAE; assess Pearson correlations between covariates and residuals (SC‑005). | Results added to `results/covariate_impact.json` and discussed in the final report. |
| **1️⃣1️⃣ Visualization & Report** | `generate_report.py` – training curve, parity plot, substructure importance chart (FR‑007); assemble manifest (Principle IV). | Final `report/` directory ready for paper stage. |
| **🧭 Resource Monitoring** | `logger.py` records wall‑clock time (SC‑002) and peak RAM (SC‑003); aborts if > 6 h or > 7 GB RAM (FR‑008). | Logs inspected; CI job respects 6 h / 7 GB caps. |

## Timeline (estimated on CI runner)

| Phase | Approx. Time |
|-------|--------------|
| Data download & checksum | < 5 min |
| Cleaning & scaffold split | 12 min |
| Feature extraction | 14 min |
| GNN training (≤ 50 epochs) | 2 h 20 min |
| Baseline training & evaluation | 6 min |
| IG & SHAP consistency check (100 molecules) | 45 min |
| Substructure aggregation & validation | 10 min |
| Covariate impact analysis | 8 min |
| Visualization & report generation | 8 min |
| **Total** | **≈ 3 h 33 min** (well under the 6 h limit) |