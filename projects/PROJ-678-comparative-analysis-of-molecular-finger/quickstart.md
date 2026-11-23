# Quickstart – End‑to‑End Execution

This document lists the commands that constitute the full analysis
pipeline. The commands are ordered to respect the data contracts
defined in the specification.

```bash
# 1️⃣ Download the raw Tox21 dataset.
python code/download.py

# 2️⃣ Filter for organophosphate compounds.
python code/filter.py

# 3️⃣ Generate molecular fingerprints.
python code/fingerprints.py

# 4️⃣ Create training / test splits (single split + K‑fold).
python code/split.py

# 5️⃣ Train models (final model + K‑fold cross‑validation).
python code/train.py

# 6️⃣ Evaluate and generate the final research report.
python code/evaluate.py
```

The unit tests for the statistical utilities can be run independently
with:

```bash
pytest tests/unit/test_stats.py
```

Ensure all tests pass, particularly `test_filter.py` (SMARTS pattern) and `test_fingerprints.py` (bit lengths).

## Validation

To verify that the entire pipeline completes within the CI time budget (60 minutes), run:

```bash
python code/quickstart_validation.py
```

The script will write a short report to `data/processed/quickstart_validation.txt`.