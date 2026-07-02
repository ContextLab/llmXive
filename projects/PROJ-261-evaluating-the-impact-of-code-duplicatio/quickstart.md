# Quickstart – end‑to‑end execution

This document describes the commands required to reproduce the full analysis
pipeline from raw data acquisition to final visualizations. All commands are
intended to be run from the project root.

```bash
# 1️⃣ Install dependencies (run once)
pip install -r requirements.txt

# 2️⃣ Stream a small sample of the GitHub‑code corpus (produces
# data/raw/github-code-sample.csv)
python code/data_loader.py

# 3️⃣ Scan for PII (writes any findings to data/analysis/pii_findings.csv) [UNRESOLVED-CLAIM: c_a3e4bc83 — status=refuted]
python code/pii_scanner.py

# 4️⃣ Compute clone density (produces data/processed/clone_metrics.csv) [UNRESOLVED-CLAIM: c_1ee32ee6 — status=not_enough_info]
python -c "import code.ast_cloner as ac; ac.compute_clone_density_batch()"

# 5️⃣ Load the model and compute perplexity scores
# (produces data/processed/perplexity_scores.csv)
python code/model_metrics.py

# 6️⃣ Run bug‑detection on the HumanEval subset
# (produces data/processed/bug_detection_results.csv)
python code/bug_detection.py

# 7️⃣ Correlation analysis (produces data/analysis/correlation_results.csv) [UNRESOLVED-CLAIM: c_f18d65e0 — status=not_enough_info]
python code/correlation_analysis.py

# 8️⃣ Generate visualizations (figures saved under
# data/analysis/figures/)
python code/visualization/plotting.py

# 9️⃣ {{claim:c_225ee0aa}} (Wikidata Q20748093, https://www.wikidata.org/wiki/Q20748093)
python code/quickstart_validation.py
```

## Memory‑monitoring (SC‑002)

The pipeline automatically enforces a 7 GB RAM limit during model inference. [UNRESOLVED-CLAIM: c_1262c408 — status=not_enough_info]
The limit is configured in ``code/config.py`` (``get_memory_limit_mb``) and
is activated by ``code.memory_monitor.setup_memory_monitoring`` which is
invoked internally by ``code.model_metrics``. If the limit is exceeded a
``MemoryError`` will be raised and the pipeline will abort, ensuring the
resource constraint is respected.
