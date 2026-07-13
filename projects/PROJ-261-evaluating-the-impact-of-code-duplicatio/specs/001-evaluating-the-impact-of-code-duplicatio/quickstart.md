# Quickstart – end‑to‑end execution

This document describes the commands that constitute a full run of the
research pipeline. The commands are deliberately ordered to respect data
dependencies.

```bash
# 1️⃣ Stream a small sample of the CodeParrot/GitHub‑Code dataset
python code/data_loader.py

# 2️⃣ Scan for PII in the freshly downloaded data
python code/pii_scanner.py

# 3️⃣ Compute clone density metrics
python code/ast_cloner.py

# 4️⃣ Compute model perplexity (and semantic distance)
python code/model_metrics.py

# 5️⃣ Run bug‑detection evaluation on HumanEval
python code/bug_detection.py

# 6️⃣ **Generate correlation results (T034)**
python code/save_correlation_results.py

# 7️⃣ Produce visualisations (scatter plots, sensitivity analysis)
python code/visualization/plotting.py

# 8️⃣ Validate that all expected outputs exist
python code/quickstart_validation.py
```

After the final step completes, you should find the following artefacts:

- `data/processed/clone_metrics.csv`
- `data/processed/perplexity_scores.csv`
- `data/processed/bug_detection_results.csv`
- `data/analysis/correlation_results.csv`
- `data/analysis/figures/` (PNG & PDF visualisations)