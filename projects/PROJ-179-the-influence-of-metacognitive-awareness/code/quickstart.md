# Quickstart

This file documents the commands required to run the full analysis pipeline
from a fresh checkout. All commands are intended to be executed from the
repository root.

```bash
# 1. Validate data availability (gate)
python code/data/validate_data_availability.py

# 2. Download the behavioural dataset
python code/data/download.py

# 3. Validate the downloaded CSV(s)
python code/data/validate_data.py

# 4. Pre‑process raw data into trial‑wise format
python code/data/preprocess.py

# 5. Compute the correlation (hold‑out design)
python -m src.analysis.correlation

# 6. Run the bootstrap for confidence intervals
python -m src.analysis.bootstrap

# 7. Generate the final report (primary analysis)
python -m src.report.generate
```

After the last step you should find the JSON report at
`data/results/primary_analysis.json`.