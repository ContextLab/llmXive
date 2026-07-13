# Quickstart Guide: llmXive PlanBench-XL Extension

This guide walks you through the end-to-end execution of the experiment to compare Baseline and Augmented agents on the synthetic implicit failure subset of PlanBench-XL.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- At least 7GB of available RAM (CPU-only execution)
- Internet connection (for downloading the dataset)

## Step 1: Environment Setup

1. **Activate Virtual Environment**:
 ```bash
 cd projects/PROJ-871-llmxive-follow-up-extending-planbench-xl
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Step 2: Project Initialization

1. **Create Directory Structure**:
 ```bash
 python code/setup_dirs.py
 ```
 This script ensures `code/`, `data/`, `tests/`, and their subdirectories exist.

## Step 3: Data Preparation

1. **Download PlanBench-XL**:
 ```bash
 python code/dataset/loader.py
 ```
 - Downloads the dataset from HuggingFace.
 - Saves raw data to `data/raw/planbench_xl.parquet`.

2. **Inject Synthetic Failures**:
 ```bash
 python code/dataset/injector.py
 ```
 - Selects success tasks (seed=42).
 - Injects `ERROR: silent_tool_failure` into tool outputs.
 - Outputs `data/derived/implicit_failure_subset.jsonl`.

3. **Build Failure Signature Index**:
 ```bash
 python code/dataset/indexer.py
 ```
 - Parses injected errors.
 - Creates `data/derived/failure_signatures.json`.

## Step 4: Agent Execution

1. **Run Baseline Agent**:
 ```bash
 python code/run_baseline.py
 ```
 - Executes tasks using internal reasoning only.
 - Logs results to `data/logs/baseline_execution.jsonl`.

2. **Run Augmented Agent**:
 ```bash
 python code/run_augmented.py
 ```
 - Executes tasks with signature-based recovery.
 - Logs results to `data/logs/augmented_execution.jsonl`.

## Step 5: Analysis & Reporting

1. **Generate Final Report**:
 ```bash
 python code/analysis/report.py
 ```
 - Aggregates logs from both agents.
 - Performs statistical testing (Fisher's Exact or Z-test).
 - Outputs `data/results/final_report.json`.

## Step 6: Verification

1. **Run Tests**:
 ```bash
 pytest tests/ -v
 ```
 - Verifies data loading, injection logic, and statistical calculations.

2. **Check Outputs**:
 Ensure the following files exist:
 - `data/derived/implicit_failure_subset.jsonl`
 - `data/derived/failure_signatures.json`
 - `data/logs/baseline_execution.jsonl`
 - `data/logs/augmented_execution.jsonl`
 - `data/results/final_report.json`

## Troubleshooting

- **Memory Errors**: Ensure you are using a quantized model (4-bit/8-bit) and have closed other RAM-intensive applications.
- **Dataset Download Failures**: Check your internet connection and HuggingFace token configuration if required.
- **Import Errors**: Verify that `code/` is in your Python path or run scripts from the project root.

## Next Steps

- Review `data/results/final_report.json` for statistical significance.
- Analyze specific failure cases in the execution logs.
- Extend the failure injection logic to include other error patterns.