# Quickstart for *The Influence of Metacognitive Awareness on Reality Testing*

This document provides the minimal commands required to run the full analysis
pipeline from end‑to‑end. All commands assume they are executed from the
repository root.

```bash
# 1️⃣ Install required dependencies
pip install -r requirements.txt

# 2️⃣ Validate data availability (T004)
python -m data.validate_data_availability

# 3️⃣ Download the verified dataset (T005)
python -m data.download

# 4️⃣ Validate the downloaded dataset (T006)
python -m data.validate_data

# 5️⃣ Pre‑process the raw data (T012)
python -m data.preprocess

# 6️⃣ Compute the primary correlation (T014) and bootstrap CI (T015)
python -m src.analysis.correlation
python -m src.analysis.bootstrap

# 7️⃣ Run modality‑specific robustness analysis (T026‑T027)
python -m src.analysis.filter
python -m src.analysis.robustness

# 8️⃣ Generate the final JSON reports (T016 & T028)
python -m src.report.generate

# 9️⃣ (Optional) Validate that the expected output files exist
python -m quickstart_validator
```

After the final step you should find the two result files:

- `data/results/primary_analysis.json`
- `data/results/robustness_analysis.json`

These files contain the correlation statistics and the corrected modality‑specific
p‑values, respectively.