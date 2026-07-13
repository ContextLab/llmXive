# Quickstart Run‑Book

This document lists the commands that must be executed in order to generate all
research artefacts for the project.

```bash
# 1️⃣ Download a small sample of the GitHub‑code corpus
python code/data_loader.py

# 2️⃣ Run the main US‑1 pipeline (clone density & perplexity)
python code/main.py

# 3️⃣ Run bug‑detection (US‑2) – already implemented in previous tasks
python code/bug_detection.py

# 4️⃣ Generate correlation results (US‑2)
python code/generate_correlation_results.py

# 5️⃣ Produce visualisations (US‑3)
python code/visualization/plotting.py

# 6️⃣ Validate that all expected artefacts exist
python code/quickstart_validation.py
```

After the above commands complete without error, the following files should be present:

- `data/processed/clone_metrics.csv`
- `data/processed/perplexity_scores.csv`
- `data/processed/bug_detection_results.csv`
- `data/analysis/correlation_results.csv`
- `data/analysis/figures/` (PNG/PDF plots)

The validation step will raise an error if any of these are missing.