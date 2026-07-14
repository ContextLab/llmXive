# Quick‑start Run‑book

This document lists the commands that constitute a full end‑to‑end run of the
research pipeline. Running the commands in the order shown will:
 1. Download the QM9 dataset,
 2. Create a reproducible 10 k molecule subset,
 3. Generate the processed parquet artefacts,
 4. Train the GNN and Random‑Forest baselines,
 5. Produce performance plots and significance analysis,
 6. Summarise the results,
 7. Validate that all expected artefacts exist.

```bash
# 1️⃣ Download raw QM9 data (handles DOI fall‑back)
python code/data/download_qm9.py

# 2️⃣ Create a reproducible 10 k subset [UNRESOLVED-CLAIM: c_8bd58b5c — status=not_enough_info]
python code/data/create_subset.py

# 3️⃣ Generate processed parquet files (the artefact this task implements)
python code/data/generate_processed_data.py

# 4️⃣ Train the SchNet‑style GNN (5 seeds, early‑stopping, 50 epochs)
python code/training/train_gnn.py

# 5️⃣ Train the Random‑Forest baseline (5 seeds)
python code/training/train_rf.py

# 6️⃣ Produce performance plots
python code/analysis/generate_performance_plots.py

# 7️⃣ Compute statistical significance of the performance gap
python code/analysis/generate_significance.py

# 8️⃣ Assemble the final markdown summary
python code/generate_summary.py

# 9️⃣ Validate that the quick‑start succeeded (checks for all declared files)
python code/quickstart_validation.py
```