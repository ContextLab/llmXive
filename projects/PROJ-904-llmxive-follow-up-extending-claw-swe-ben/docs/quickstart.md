# Quickstart Guide: llmXive Context Fidelity vs. Model Scaling

This guide provides instructions for setting up and running the `llmXive` automated science pipeline experiments.

## Prerequisites

- Python 3.11+
- Access to Hugging Face Hub (token required for model downloads)
- Minimum 16GB RAM (7B model) or 8GB RAM (1B model)
- Internet connection for dataset streaming

## Setup

1. **Clone and Navigate**
 ```bash
 cd projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/
 ```

2. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

3. **Configure Environment**
 Set the following environment variables:
 ```bash
 export HF_TOKEN="your_huggingface_token"
 export PYTHONPATH="."
 export RANDOM_SEED=42
 ```

## Data Pipeline

The project uses `ClawSweBenchLoader` to stream data from Hugging Face. No local dataset files are required initially.

### Run Baseline (User Story 1)
Executes a naive "first-N-lines" context strategy with a 1B model.
```bash
python experiments/run_baseline.py
```
**Output**: `data/intermediate/baseline_run.jsonl`

### Run High-Fidelity (User Story 2 & 3)
Executes TF-IDF, Diff-Aware, and Semantic Summarization strategies.
- **1B Model**:
 ```bash
 python experiments/run_high_fidelity.py --model-size 1B
 ```
 **Output**: `data/intermediate/hf_run_1b.jsonl`
- **7B Model**:
 ```bash
 python experiments/run_high_fidelity.py --model-size 7B
 ```
 **Output**: `data/intermediate/hf_run_7b.jsonl`

## Analysis

### Merge Results
Aggregates all experiment runs into a single CSV for analysis.
```bash
python analysis/merge_results.py
```
**Output**: `data/results.csv`

### GLM Interaction Analysis
Performs Generalized Linear Mixed Model analysis to test for interaction effects between context strategy and model size.
```bash
python analysis/glm_analyzer.py
```
**Output**: `data/analysis/post_hoc_results.json`

### Failure Classification
Classifies execution failures as "missing context" or "reasoning error".
```bash
python analysis/failure_classifier.py
```

## Validation

To verify the dependency graph reconstruction logic:
```bash
python data/loader.py --validate
```
**Output**: `data/validation_report.json`

## Troubleshooting

- **Memory Errors**: If the 7B model exceeds 7GB RAM with Q4_K_M quantization, the system raises `MemoryConstraintError`. Ensure sufficient RAM or switch to CPU offloading in `config.py`.
- **Dataset Fetch Failures**: The loader fails loudly if the Hugging Face stream cannot be accessed. Check your `HF_TOKEN` and internet connection.
- **Timeouts**: The `BatchExecutor` enforces a 60-minute per-instance budget and a 72-hour total wall-clock limit.

## Project Structure

```
code/
├── config.py # Configuration and data classes
├── data/
│ ├── loader.py # ClawSweBench data loading
│ └── context_processors.py # Context compression strategies
├── experiments/
│ ├── batch_executor.py # Parallel execution manager
│ ├── run_baseline.py # Baseline experiment script
│ └── run_high_fidelity.py # High-fidelity experiment script
├── models/
│ └── runner.py # Model loading and inference
├── analysis/
│ ├── merge_results.py # Data aggregation
│ ├── failure_classifier.py # Error classification
│ └── glm_analyzer.py # Statistical analysis
└── tests/ # Unit and integration tests
```
