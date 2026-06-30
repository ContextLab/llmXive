# Quickstart

This document describes the steps required to run the full analysis pipeline.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the data loader (creates raw CSV)
python -m code.data_loader

# Run the pipeline (creates processed metrics)
python code/main.py

# Validate that the expected files were produced
python code/quickstart_validation.py
```

After these commands complete without error, the research artefacts are ready.