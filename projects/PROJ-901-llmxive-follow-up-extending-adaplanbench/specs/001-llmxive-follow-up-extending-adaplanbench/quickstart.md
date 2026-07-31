# Quickstart: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for dataset download, optional if using proxy)
- GB+ RAM available

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-901-llmxive-follow-up-extending-adaplanbench
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Data Fetch and Filter
Fetches the AdaPlanBench dataset (or generates a synthetic proxy) and filters for tasks with ≥5 constraints.
```bash
python code/dataset/loader.py --filter-constraints 5
```
*Output*: `data/processed/filtered_tasks.csv`, `data/raw/validation_report.json`

### 2. Power Analysis
Runs a power analysis to confirm sample size sufficiency.
```bash
python code/analysis/power.py --input data/processed/filtered_tasks.csv
```
*Output*: `data/processed/power_report.json`

### 3. Agent Execution
Runs both Dual-Track and Monolithic architectures on the filtered dataset.
```bash
python code/main.py --mode execution
```
*Outputs*: `data/processed/dual_track_logs.json`, `data/processed/monolithic_logs.json`, `data/processed/resource_logs.json`

### 4. Human Annotation Sampling
Generates a stratified sample for manual review.
```bash
python code/dataset/annotator.py --sample-size 50
```
*Output*: `data/annotations/annotation_sample.csv`

### 5. Statistical Analysis
Fits the GLMM and generates the final results.
```bash
python code/analysis/glmm.py --input data/processed/execution_traces.csv
```
*Output*: `data/processed/statistical_results.json`, `data/processed/agreement_rate_report.json`

## Verification

- **Check Data**: Verify `data/processed/filtered_tasks.csv` exists and has the expected number of rows.
- **Check Logs**: Ensure `data/processed/resource_logs.json` shows no `threshold_exceeded: true` events.
- **Check Stats**: Confirm `data/processed/statistical_results.json` contains a p-value for the interaction term.

## Troubleshooting

- **Dataset Fetch Failed**: If `loader.py` fails to fetch AdaPlanBench, it will automatically generate a synthetic proxy. Check `data/raw/validation_report.json` for details.
- **Memory Error**: If RAM exceeds available system limits, reduce the batch size in `code/main.py` or use streaming mode.
- **GLMM Convergence**: If the model fails to converge, check for sparse data in high constraint bins. The pipeline will attempt to use Firth's penalized likelihood.
