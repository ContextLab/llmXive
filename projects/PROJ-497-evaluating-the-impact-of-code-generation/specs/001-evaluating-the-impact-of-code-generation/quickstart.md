# Quickstart: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM (for model loading)
- GB+ Disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-497-evaluating-the-impact-of-code-generation
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### 1. Download Datasets
Download the HumanEval and MBPP datasets.
```bash
python code/download.py --datasets humaneval mbpp
```
*Output*: `data/raw/humaneval.parquet`, `data/raw/mbpp.parquet`

### 2. Generate Code Samples
Generate code samples for StarCoder and CodeGen models.
```bash
python code/generate.py --models starcoder codegen --benchmarks humaneval mbpp --samples-per-task
```
*Output*: `data/generated/`, `data/processed/valid_samples.csv`

### 3. Run Static Analysis
Analyze generated and human code for vulnerabilities.
```bash
python code/analyze.py --input data/generated data/human --tool bandit --config code/config/bandit_config.yaml
```
*Output*: `data/processed/vulnerability_reports.json`

### 4. Aggregate Data
Aggregate LLM samples per task to match Human references.
```bash
python code/aggregate.py --input data/processed/vulnerability_reports.json
```
*Output*: `data/processed/aggregated_analysis_dataset.csv`

### 5. Statistical Analysis
Run ZINB regression and permutation tests.
```bash
python code/stats.py --input data/processed/aggregated_analysis_dataset.csv
```
*Output*: `results/statistical_results.json`

### 6. Generate Visualizations
Create plots and the final report.
```bash
python code/viz.py --input results/statistical_results.json
python code/report.py --input results/statistical_results.json
```
*Output*: `results/plots/`, `results/summary.md`

## Verification

To verify reproducibility:
1.  Run the pipeline with the same random seed.
2.  Compare `results/statistical_results.json` with the previous run.
3.  Checksums in `state/artifact_hashes.yaml` should match.

## Troubleshooting

- **OOM Error**: Reduce `--samples-per-task` or switch to a smaller model variant.
- **Bandit Parse Error**: Skip files with syntax errors (handled automatically).
- **ZINB Convergence Failure**: The pipeline automatically falls back to permutation tests.
