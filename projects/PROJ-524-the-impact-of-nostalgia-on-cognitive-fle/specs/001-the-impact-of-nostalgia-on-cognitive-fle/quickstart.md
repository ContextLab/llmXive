# Quick Start Guide

This guide explains how to set up and run the llmXive pipeline for PROJ-524: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults.

## Prerequisites

- Python 3.9+
- pip
- git

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Ensure data directories exist** (Run T001):
 ```bash
 python code/setup_dirs.py
 ```

## Running the Pipeline

The pipeline is executed in stages. You can run the full orchestration or individual tasks.

### Option A: Full Orchestration (Recommended)

Run the main orchestration script which handles data ingestion, cleaning, analysis, and reporting:

```bash
python code/main.py
```

This command will:
1. Fetch or simulate data.
2. Clean and filter the data.
3. Run statistical analysis (Welch's t-test).
4. Perform robustness checks (T027b).
5. Generate final reports.

### Option B: Step-by-Step Execution

If you need to debug specific stages, run the tasks individually in order:

1. **Ingestion & Simulation**:
 ```bash
 python code/task_t010d_generate_simulation.py
 ```

2. **Data Cleaning**:
 ```bash
 python code/task_t012a_age_exclusion.py
 python code/task_t012b_score_exclusion.py
 python code/task_t012d_mmse_flag.py
 python code/task_t012e_mmse_exclusion.py
 python code/task_t014a_create_cleaned_dataset.py
 python code/task_t014b_validity_metrics.py
 ```

3. **Analysis**:
 ```bash
 python code/analysis.py
 ```

4. **Robustness Analysis (T027b)**:
 ```bash
 python code/task_t027b_mmse_robustness_analysis.py
 ```

5. **Generate Reports**:
 ```bash
 python code/generate_robustness_summary.py
 ```

## Output Artifacts

Upon successful completion, the following files will be generated:

- `data/raw/raw_dataset.csv`: Raw input data.
- `data/processed/cleaned_dataset.csv`: Primary cleaned dataset (with MMSE filter).
- `data/processed/cleaned_dataset_no_mmse.csv`: Robustness dataset (without MMSE filter).
- `data/results/statistical_report.json`: Primary statistical results.
- `data/results/robustness_report.json`: Results from the robustness analysis (T027b).
- `paper/001_results.md`: Final scientific report.

## Troubleshooting

- **KeyError: 'paths'**: Ensure `code/config.py` is correctly configured and `data/` directories exist.
- **DataNotFoundError**: Ensure the ingestion step (T010d) has successfully generated `data/raw/raw_dataset.csv`.
- **Simulation Mode**: If real data is unavailable, the pipeline automatically falls back to simulation. Check `data/raw/metadata.json` for `simulation_mode: true`.

## Verification

To verify the pipeline integrity, run the integration test:

```bash
python -m pytest tests/integration/test_full_pipeline.py -v
```