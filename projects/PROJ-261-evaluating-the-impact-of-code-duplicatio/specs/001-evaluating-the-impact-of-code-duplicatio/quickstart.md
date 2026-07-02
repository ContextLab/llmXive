# Quickstart for Evaluating Code Duplication Impact

This document provides the minimal commands required to run the full research
pipeline from end‑to‑end. All commands should be executed from the repository
root.

```bash
# 1️⃣ Install dependencies
pip install -r requirements.txt

# 2️⃣ Stream a 500 MB subset of the CodeParrot GitHub corpus [UNRESOLVED-CLAIM: c_09a28615 — status=not_enough_info]
python code/data_loader.py

# 3️⃣ Scan for PII (optional but recommended)
python code/pii_scanner.py

# 4️⃣ Compute clone density metrics
python code/ast_cloner.py

# 5️⃣ Compute model perplexity scores (8‑bit quantised)
python code/model_metrics.py

# 6️⃣ Evaluate bug‑detection (HumanEval) and compute pass@1
python code/bug_detection.py

# 7️⃣ Correlation analysis (duplication ↔ perplexity ↔ accuracy)
python code/correlation_analysis.py

# 8️⃣ Generate visualisations
python code/visualization/plotting.py

# 9️⃣ Validate that all expected artefacts exist
python code/quickstart_validation.py
```

After the above steps complete you should find the following artefacts in the
repository:

- `data/raw/github-code-sample.csv` – streamed subset of the CodeParrot corpus
- `data/processed/clone_metrics.csv` – clone‑density per file/problem
- `data/processed/perplexity_scores.csv` – token‑level perplexity per file
- `data/processed/bug_detection_results.csv` – pass@1 and clone density per HumanEval problem
- `data/analysis/correlation_results.csv` – Spearman correlation matrix and p‑values
- `data/analysis/figures/` – PNG/PDF visualisations

The quickstart validation script (`code/quickstart_validation.py`) will raise an
error if any of the above artefacts are missing or malformed.