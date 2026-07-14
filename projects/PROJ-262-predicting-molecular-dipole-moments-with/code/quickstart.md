# Quickstart Run‑Book
This file orchestrates the end‑to‑end execution of the research pipeline.
Each command is expected to exit with status 0 and produce the artefacts
declared in the specification.

```bash
# 1️⃣ Download & prepare the QM9 dataset (generates the three parquet files)
python code/data/generate_processed_data.py

# 2️⃣ Train the SchNet‑style GNN (requires the parquet files produced above)
python code/training/train_gnn.py

# 3️⃣ Train the Random‑Forest baseline
python code/training/train_rf.py

# 4️⃣ Generate performance plots
python code/analysis/generate_performance_plots.py

# 5️⃣ Compute statistical significance
python code/analysis/generate_significance.py

# 6️⃣ Produce the final summary markdown
python code/generate_summary.py
```
The quickstart validation script (`code/quickstart_validation.py`) checks that
all declared artefacts exist after the above steps. No additional manual
steps are required.