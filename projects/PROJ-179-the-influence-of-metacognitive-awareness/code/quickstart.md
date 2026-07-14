# Quickstart for PROJ-179-the-influence-of-metacognitive-awareness

This document describes the commands required to run the full analysis pipeline
from end‑to‑end. All paths are relative to the repository root.

## Prerequisites

- Python 3.9+ (ensure the virtual environment defined in `requirements.txt` is active)
- All foundational tasks (T004‑T015) have completed successfully.

## Execution steps

1. **Validate data availability**
 ```bash
 python code/data/validate_data_availability.py
 ```

2. **Download the behavioural dataset**
 ```bash
 python code/data/download.py
 ```

3. **Validate the downloaded dataset**
 ```bash
 python code/data/validate_data.py
 ```

4. **Pre‑process the raw data**
 ```bash
 python code/data/preprocess.py
 ```

5. **Run the primary correlation analysis**
 ```bash
 python code/src/analysis/correlation.py
 ```

6. **Run the bootstrap confidence‑interval procedure**
 ```bash
 python code/src/analysis/bootstrap.py
 ```

7. **Generate the primary report** *(creates `data/results/primary_analysis.json`)*
 ```bash
 python code/src/report/generate.py
 ```

8. **Run the modality‑specific robustness analysis**
 ```bash
 python code/src/analysis/robustness.py
 ```

9. **Generate the robustness report** *(creates `data/results/robustness_analysis.json`)*
 ```bash
 python code/src/report/generate.py
 ```

10. **Run any additional diagnostics / regression steps** (if required)

After the above steps complete, you should find the two JSON artefacts under
`data/results/`:

- `primary_analysis.json`
- `robustness_analysis.json`

These files are the definitive outputs verified by the integration tests.