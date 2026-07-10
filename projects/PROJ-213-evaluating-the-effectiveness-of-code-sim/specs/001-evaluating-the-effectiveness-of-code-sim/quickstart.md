# Quick Start Guide: Evaluating Code Simplification Effectiveness

This guide provides instructions to set up the environment and run the benchmark pipeline for evaluating the effectiveness of code simplification on LLM performance.

## Prerequisites

- Python 3.9 or higher
- Access to HuggingFace (for dataset download)
- 7GB+ RAM (for StarCoder-1.3B 4-bit model inference)

## Setup Instructions

1. **Clone the repository** (if not already done) and navigate to the project root.

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify dataset and model availability** (optional but recommended):
 ```bash
 python code/verify_dataset.py
 python code/verify_model.py
 ```

## Running the Benchmark Pipeline

The full pipeline consists of three main stages: **Download**, **Simplify**, and **Inference/Analysis**.

### Option A: Run the Full Pipeline (Orchestrated)

Execute the main orchestration script to run the complete benchmark:

```bash
python code/main.py
```

This will:
1. Download the HumanEval dataset.
2. Generate AST-simplified versions of the code.
3. Run inference on both raw and simplified code using the StarCoder-1.3B model.
4. Generate result tables (`data/processed/results_raw.csv`, `data/processed/results_simplified.csv`).
5. Perform statistical analysis and generate `analysis_report.pdf`.

### Option B: Run Stages Independently

If you need to run specific stages separately:

#### 1. Download Dataset
```bash
python code/download.py
```
**Output**: `data/raw/humaneval.json` (and checksums in `state/map.json`)

#### 2. Simplify Code
```bash
python code/simplify.py
```
**Outputs**:
- `data/processed/simplified_problems.json`
- `data/logs/parse_failures.log`
- `data/logs/flagged_snippets.csv`

#### 3. Run Inference & Analysis
```bash
python code/inference.py --mode full
python code/analyze.py
```
**Outputs**:
- `data/processed/metrics_raw.csv`
- `data/processed/metrics_simplified.csv`
- `analysis_report.pdf`
- `figures/accuracy_latency_comparison.png`

## Expected Outputs

After a successful run, you should find the following artifacts in the project root:

- **Data**:
 - `data/raw/humaneval.json`
 - `data/processed/simplified_problems.json`
 - `data/processed/results_raw.csv`
 - `data/processed/results_simplified.csv`
 - `data/processed/metrics_raw.csv`
 - `data/processed/metrics_simplified.csv`
- **Logs**:
 - `data/logs/parse_failures.log`
 - `data/logs/flagged_snippets.csv`
- **Reports**:
 - `analysis_report.pdf`
 - `figures/accuracy_latency_comparison.png`
- **State**:
 - `state/map.json` (artifact versioning and checksums)

## Troubleshooting

- **Memory Error**: Ensure you have at least 7GB of free RAM. The StarCoder-1.3B 4-bit model requires significant memory.
- **Dataset Download Failed**: Verify your internet connection and HuggingFace token (if required).
- **Inference Timeout**: The default timeout is 30 seconds per sample. Increase `TIMEOUT_SECONDS` in `code/config.py` if necessary (not recommended for standard runs).

## Next Steps

- Review `research.md` for statistical design and power analysis details.
- Check `specs/001-eval-code-simplification/spec.md` for detailed user stories and requirements.
- Run tests in `tests/` to validate the pipeline.