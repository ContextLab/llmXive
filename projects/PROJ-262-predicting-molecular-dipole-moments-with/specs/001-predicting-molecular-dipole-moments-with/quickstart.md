# Quickstart – end‑to‑end run‑book

This document lists the commands that constitute a full pipeline execution.
Run the commands **in the order shown** from the repository root.

```bash
# 1️⃣ Download the raw QM9 dataset
python projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py

# 2️⃣ Create a reproducible 10 k random subset [UNRESOLVED-CLAIM: c_56d10258 — status=not_enough_info]
python projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py

# 3️⃣ Extract simple 3‑D geometry features
python projects/001-predicting-molecular-dipole-moments/code/data/preprocess_3d.py

# 4️⃣ Generate lightweight 2‑D descriptors
python projects/001-predicting-molecular-dipole-moments/code/data/extract_2d_descriptors.py

# 5️⃣ (Placeholder) Train the GNN model – already implemented elsewhere
python projects/001-predicting-molecular-dipole-moments/code/training/train_gnn.py

# 6️⃣ (Placeholder) Train the Random Forest baseline
python projects/001-predicting-molecular-dipole-moments/code/training/train_rf.py

# 7️⃣ Generate performance plots
python code/analysis/generate_performance_plots.py

# 8️⃣ Generate summary report
python code/generate_summary.py
```

After the run‑book finishes, you should find the following artefacts in the
repository:

* `data/processed/molecules_10k.parquet` – the curated subset.
* `data/processed/features_3d.parquet` – simple 3‑D geometry features.
* `data/processed/features_2d.parquet` – atom‑type histogram descriptors.
* Model checkpoints, metrics CSV, figures, and summary JSON as described in
 the spec.