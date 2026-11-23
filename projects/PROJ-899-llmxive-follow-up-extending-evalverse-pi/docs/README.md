# llmXive: Extending EvalVerse with CPU-tractable Feature Distillation

## Overview
llmXive is an automated science pipeline designed to evaluate the viability of low-level video and audio features (optical flow, HOG, spectral centroid, etc.) as proxies for human expert scores on technical video dimensions. The project aims to determine which dimensions are "feature-sufficient" (high correlation with low-level features) versus "VLM-required" (requiring high-level visual-language models).

## Project Structure
```
.
├── code/
│ ├── src/
│ │ ├── cli/
│ │ ├── data/
│ │ ├── models/
│ │ ├── reports/
│ │ ├── config.py
│ │ └── utils.py
│ ├── scripts/
│ ├── tests/
│ └──...
├── data/
│ ├── raw/ # Downloaded EvalVerse dataset
│ ├── processed/ # Extracted feature vectors
│ └── results/ # Correlation and profiling outputs
├── state/ # Pipeline state and gate results
├── reports/ # Final feasibility and sensitivity reports
├── docs/ # Documentation
└── specs/ # Design documents
```

## Prerequisites
- Python 3.11+
- CPU-only environment (GPU not required)
- Dependencies listed in `requirements.txt`

## Installation
```bash
pip install -r requirements.txt
```

## Quick Start
1. **Setup Environment**:
 ```bash
 python code/scripts/setup_environment.py
 ```
 This initializes directory structures and verifies the environment.

2. **Download Data**:
 ```bash
 python code/scripts/download.py
 ```
 Fetches the EvalVerse dataset from Zenodo (defined in `src/config.py`).

3. **Verify Data**:
 ```bash
 python code/scripts/checksum_data.py
 ```
 Validates the downloaded dataset integrity.

4. **Run Pipeline**:
 ```bash
 python code/scripts/run_pipeline.py
 ```
 Executes the full analysis: feature extraction, model training, correlation analysis, and profiling.

5. **Generate Reports**:
 ```bash
 python code/scripts/generate_timing_profile.py
 python code/scripts/generate_sensitivity_analysis.py
 python code/scripts/generate_sensitivity_matrix.py
 ```

## Key Outputs
- `data/baseline_results.csv`: Baseline model comparisons
- `data/permutation_results.csv`: Multiple-comparison corrected results
- `data/timing_profile.csv`: Projected inference times for 10k clips
- `data/sensitivity_analysis.csv`: Threshold stability analysis
- `reports/feasibility_profile.json`: Final feasibility report
- `state/validation_status.json`: VLM proxy validation status

## Configuration
All configuration constants (dataset URLs, seeds, thresholds) are defined in `code/src/config.py`.

## Testing
Run tests using pytest:
```bash
pytest code/tests/
```

## License
[Insert License]
