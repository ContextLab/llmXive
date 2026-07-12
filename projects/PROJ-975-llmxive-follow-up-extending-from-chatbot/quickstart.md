# llmXive Quickstart Guide

This guide provides end-to-end execution steps for the "From Chatbot to Digital Colleague" experiment pipeline (Project PROJ-975).

## Prerequisites

- Python 3.9+
- pip (Python package installer)
- At least 8GB RAM (for embedding calculations) [UNRESOLVED-CLAIM: c_6f56bb25 — status=not_enough_info]

## 1. Setup Environment

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd projects/PROJ-975-llmxive-follow-up-extending-from-chatbot

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Project Initialization

Run the setup scripts to create the required directory structure and configuration files.

```bash
# Create directory structure (data/raw, data/results, code, tests, contracts)
python code/setup_directories.py

# Initialize contract schemas (task, skill, experiment_log)
python code/setup_contracts.py
```

## 3. Data Generation (User Story 1)

Generate the synthetic dataset containing 500 multi-step tasks and 100 overlapping skills. [UNRESOLVED-CLAIM: c_2eb18040 — status=not_enough_info]

```bash
# Set random seeds for reproducibility (optional, defaults used if not set)
export SEED_A=42
export SEED_B=123

# Run data generation
python code/generate_data.py
```

**Expected Outputs:**
- `data/raw/skills.json`: 100 Python skill definitions with embeddings [UNRESOLVED-CLAIM: c_a22bf2c0 — status=not_enough_info]
- `data/raw/tasks.json`: 500 multi-step tasks with ground-truth solution paths [UNRESOLVED-CLAIM: c_5969827a — status=not_enough_info]
- Console output showing mean pairwise similarity and memory usage check

**Verification:**
```bash
# Verify files exist and contain data
python -c "import json; d=json.load(open('data/raw/skills.json')); print(f'Skills: {len(d[\"skills\"])}')"
python -c "import json; d=json.load(open('data/raw/tasks.json')); print(f'Tasks: {len(d[\"tasks\"])}')"
```

## 4. Baseline Experiment (User Story 3 - Pruning Disabled)

Run the full experiment with **pruning disabled** to establish a performance baseline.

```bash
python code/run_baseline.py
```

**Expected Outputs:**
- `data/results/experiment_log_baseline.csv`: Experiment logs with pruning disabled

**Verification:**
```bash
head -n 5 data/results/experiment_log_baseline.csv
```

## 5. Main Experiment (User Story 2 - With Pruning)

Run the main experiment across varying library sizes (10, 30, 50, 100) [UNRESOLVED-CLAIM: c_61793a69 — status=not_enough_info] with the "Safe Pruning" heuristic enabled.

```bash
python code/run_experiment.py
```

**Expected Outputs:**
- `data/results/experiment_log.csv`: Full experiment logs with pruning metrics
- `data/results/metrics.json`: Aggregated metrics per library size

**Verification:**
```bash
# Check that the log contains the required columns
head -n 1 data/results/experiment_log.csv
```

## 6. Analysis (User Story 3)

Perform statistical analysis to identify the "tipping point" and evaluate pruning efficacy.

```bash
python code/analyze.py
```

**Expected Outputs:**
- `data/results/final_analysis.json`: Tipping point, p-values, and VIF metrics
- `data/results/sensitivity_report.json`: Sensitivity analysis results

**Verification:**
```bash
cat data/results/final_analysis.json | python -m json.tool
```

## 7. Full End-to-End Reproducibility

To reproduce the entire pipeline from scratch:

```bash
# 1. Setup
python code/setup_directories.py
python code/setup_contracts.py

# 2. Data Generation
python code/generate_data.py

# 3. Baseline (Pruning Disabled)
python code/run_baseline.py

# 4. Main Experiment (Pruning Enabled)
python code/run_experiment.py

# 5. Analysis
python code/analyze.py

# 6. Verify Results
ls -lh data/results/
```

## Troubleshooting

- **Memory Limit Exceeded**: If you encounter memory errors during embedding calculation, ensure you have at least 8GB RAM. You may need to reduce the library size in `code/config.py`.
- **Missing Dependencies**: If `pip install` fails, ensure you are using Python 3.9+ and that your `pip` is up to date.
- **Schema Validation Errors**: If contract tests fail, re-run `code/setup_contracts.py` to regenerate the schema files.

## Next Steps

- Review the `data/results/final_analysis.json` for insights on the tipping point library size.
- Examine `data/results/sensitivity_report.json` to understand the robustness of the pruning heuristic.
- Extend the experiment by modifying the pruning threshold or overlap level in `code/config.py`.