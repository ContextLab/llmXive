# Quickstart: Evaluating the Impact of Code Generation Models on Code Vulnerability Density

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- ≥ 7GB RAM, ≥ 14GB disk
- Internet access (for dataset/model downloads)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-497-evaluating-the-impact-of-code-generation
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

   **requirements.txt** (pinned versions):
   ```text
   transformers==4.35.0
   datasets==2.14.0
   bandit==1.7.5
   scipy==1.11.3
   statsmodels==0.14.0
   pandas==2.1.3
   matplotlib==3.8.2
   seaborn==0.13.0
   pytest==7.4.3
   bitsandbytes==0.41.0  # For 8-bit quantization (CPU-compatible)
   ```

## Running the Pipeline

### Step 1: Download Benchmarks
```bash
python code/generate.py --download-benchmarks
```
- Downloads HumanEval and MBPP to `data/raw/`.
- Checksums recorded in `state/`.

### Step 2: Generate Code Samples
```bash
python code/generate.py --model starcoder --benchmark humaneval --target-samples 64 --fixed-tasks 128
python code/generate.py --model codegen --benchmark mbpp --target-samples 64 --fixed-tasks 128
```
- Generates code samples for a **fixed set of tasks** until 64 valid samples (passing tests) or 200 attempts.
- Outputs to `data/generated/`.

### Step 3: Run Static Analysis
```bash
python code/analyze.py --input-dir data/generated
```
- Runs Bandit on all generated and human code samples.
- Outputs vulnerability reports to `data/processed/vuln_reports/`.

### Step 4: Measure Complexity
```bash
python code/analyze.py --measure-complexity --input-dir data/generated
```
- Calculates Cyclomatic Complexity for all samples.
- Outputs `data/processed/complexity_metrics.csv`.

### Step 5: Estimate FPR (Sensitivity Analysis)
```bash
python code/validator.py --input-dir data/processed/vuln_reports --sample-size 20
```
- Estimates group-specific FPRs.
- Outputs `data/processed/fpr_metrics.json`.

### Step 6: Adjust Counts & Statistical Analysis
```bash
python code/stats.py --input-dir data/processed
```
- Adjusts vulnerability counts using FPR (sensitivity only).
- Runs **Permutation Test** on raw counts.
- Outputs `data/processed/stats_results.json`.

### Step 7: Generate Visualizations & Report
```bash
python code/viz.py --input-dir data/processed
python code/report.py --input-dir data/processed --output results/summary.md
```
- Generates boxplots, bar charts to `results/plots/`.
- Creates `results/summary.md` with stats, images, and sensitivity metrics.
- **Note**: Primary conclusion is based on raw counts.

## Testing

Run unit and integration tests:
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/
```

## Troubleshooting

- **OOM Errors**: If models exceed 7GB RAM, switch to smaller variants (e.g., `starcoderbase-1b`) or reduce target samples.
- **Permutation Test**: If sample size is too small, the test will fail gracefully and flag the dataset as 'under-powered'.
- **Bandit Failures**: Syntax errors in generated code are logged and excluded; no crash.