# Quickstart: Evaluating the Impact of LLM-Generated Code on Memory Usage

## Prerequisites

-   Python 3.11+
-   Sufficient RAM (Required for CPU-only LLM inference)
-   Internet access (for dataset download)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-395-evaluating-the-impact-of-llm-generated-c
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners. Includes `lifelines` for Kaplan-Meier.*

## Running the Pipeline

The pipeline is executed sequentially via CLI scripts.

### Step 1: Download Benchmark Data
```bash
python code/download.py --dataset humaneval --output data/raw/
```
*Verifies checksums and saves to `data/raw/humaneval.parquet`. If <50 pairs found, it will automatically attempt MBPP.*

### Step 2: Generate LLM Solutions
```bash
python code/generate.py --model tinyllama-1.1b --n-50 --output data/processed/llm_solutions.csv
```
*Generates solutions for a set of problems using TinyLlama-1.1B. Attempts 8-bit quantization first, falls back to float16 if unavailable.*

### Step 3: Profile Memory Usage
```bash
python code/profile.py --input data/processed/ --runs 3 --output data/processed/memory_measurements.csv
```
*Executes each solution multiple times, records peak/steady memory (steady-state = median of final portion of steps), and calculates IQR for stability.*

### Step 4: Extract Code Features
```bash
python code/features.py --input data/processed/ --output data/processed/code_features.csv
```
*Calculates LOC, Complexity, and Imports. `memory_per_loc` is calculated but excluded from modeling.*

### Step 5: Statistical Analysis
```bash
python code/analyze.py --measurements data/processed/memory_measurements.csv --features data/processed/code_features.csv --output data/processed/statistical_report.json
```
*Runs Kaplan-Meier (primary) and Wilcoxon (secondary), applies corrections, calculates VIF, and interprets effect sizes.*

## Viewing Results

-   **Raw Measurements**: `data/processed/memory_measurements.csv`
-   **Feature Data**: `data/processed/code_features.csv`
-   **Statistical Report**: `data/processed/statistical_report.json` (includes effect size magnitude)

## Troubleshooting

-   **OOM (Out of Memory)**: If the process crashes with OOM, ensure you are using the `tinyllama-1.1b` model. Reduce `n` in `generate.py` if necessary.
-   **Timeout**: If generation takes too long, the script will automatically fall back to a smaller model or skip the sample. Check `data/processed/llm_solutions.csv` for `error_type: Timeout`.
-   **Syntax Errors**: The profiler automatically handles these and records `N/A`. Review `data/processed/memory_measurements.csv` for `status: SYNTAX_ERROR`.
-   **Instability**: If IQR > 15% of median, samples are re-run. If still unstable, they are excluded from analysis.