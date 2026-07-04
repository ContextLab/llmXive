# Quickstart: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (no token required for public datasets, but recommended for rate limits)

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-726-measuring-the-carbon-footprint-of-llm-as
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed in a single command (or via GitHub Actions):

```bash
# Run the full pipeline (download, infer, calculate, analyze, report)
python code/download_data.py && \
python code/validate_baseline.py && \
python code/run_inference.py && \
python code/calculate_emissions.py && \
python code/statistical_analysis.py && \
python code/generate_report.py
```

### Step-by-Step Execution

1. **Download Data**:
   ```bash
   python code/download_data.py
   ```
   - Fetches CodeXGLUE, Human Baseline, and LOC datasets.
   - Saves to `data/raw/`.

2. **Validate Baseline**:
   ```bash
   python code/validate_baseline.py
   ```
   - Checks if human baseline data contains raw time (minutes).
   - Fails or switches to fallback if data is pre-calculated CO2.

3. **Run Inference**:
   ```bash
   python code/run_inference.py
   ```
   - Runs GPT-2-medium on target prompts with CodeCarbon.
   - Saves `data/processed/llm_inference_results.csv`.
   - **Dynamic Sample Size**: If runtime exceeds budget, reduces sample size.

4. **Calculate Emissions**:
   ```bash
   python code/calculate_emissions.py
   ```
   - Joins LLM results with human baseline (using LLM LOC as common denominator).
   - Calculates `co2_per_loc`.
   - Saves `data/processed/paired_analysis.csv`.

5. **Statistical Analysis**:
   ```bash
   python code/statistical_analysis.py
   ```
   - Runs Shapiro-Wilk, One-Sample T-Test/Wilcoxon, robustness check (DistilGPT-2).
   - Saves `data/outputs/statistical_results.json` and plots.

6. **Generate Report**:
   ```bash
   python code/generate_report.py
   ```
   - Creates `output/report.md`.

## Verification

- **Check Data**: Ensure `data/raw/` contains parquet files.
- **Check Logs**: Look for "CodeCarbon: CPU" in `run_inference.py` output.
- **Check Report**: Open `output/report.md` to view the final results.
- **Check Statistical Results**: Verify `data/outputs/statistical_results.json` contains `shapiro_wilk_p_value`.

## Troubleshooting

- **OOM Error**: Reduce `max_new_tokens` in `run_inference.py` or reduce sample size.
- **Dataset Not Found**: Verify HuggingFace connectivity.
- **CodeCarbon Error**: Ensure `codecarbon` is installed and permissions are correct for CPU measurement.
- **Baseline Validation Failure**: If `validate_baseline.py` fails, check if the source data is pre-calculated CO2. The pipeline will switch to the "General Industry Average" fallback.