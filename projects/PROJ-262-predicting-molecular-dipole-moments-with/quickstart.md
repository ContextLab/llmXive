# Quick‑start Run‑Book

This document lists the commands that the CI pipeline executes to verify the
end‑to‑end research workflow. The commands must run without error and must
produce all artefacts declared in the specification.

## Commands

```bash
# 1️⃣ Generate processed data (creates data/processed/molecules_10k.parquet)
python code/data/generate_processed_data.py

# 2️⃣ Train the GNN model (produces results/metrics.csv)
python code/training/train_gnn.py

# 3️⃣ Train the Random Forest baseline (produces results/metrics_rf.csv)
python code/training/train_rf.py

# 4️⃣ Validate the quick‑start artefacts
python code/quickstart_validation.py
```