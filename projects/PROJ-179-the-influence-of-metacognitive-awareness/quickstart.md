# Quickstart

This document describes the commands that must run successfully for the
project to be considered reproducible.

## Required steps

1. **Validate data availability**
 ```bash
 python code/data/validate_data_availability.py
 ```

2. **Download the dataset**
 ```bash
 python code/data/download.py
 ```

3. **Validate the downloaded data**
 ```bash
 python code/data/validate_data.py
 ```

4. **Preprocess the raw data**
 ```bash
 python code/data/preprocess.py
 ```

5. **Run the primary analysis pipeline**
 ```bash
 python code/src/analysis/correlation.py
 ```

6. **Bootstrap confidence intervals**
 ```bash
 python code/src/analysis/bootstrap.py
 ```

7. **Generate the primary analysis report**
 ```bash
 python -m src.report.generate
 ```

8. **Run the modality‑specific robustness analysis**
 ```bash
 python code/src/analysis/robustness.py
 ```

9. **Generate the robustness report with multiple‑comparison correction**
 ```bash
 python -m src.report.generate
 ```

After these steps, the following files should exist:

- `data/results/primary_analysis.json`
- `data/results/bootstrap_config.json`
- `data/results/robustness_analysis.json` (now contains corrected p‑values)