# Quickstart: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment for testing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-726-measuring-the-carbon-footprint-of-llm-as
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

The pipeline consists of four main steps. Run them sequentially or use the `run_all.sh` script.

### Step 1: Download Data
Downloads the CodeXGLUE dataset and validates checksums.
```bash
python code/download_data.py
```
*Output*: `data/raw/codexglue_sample.json`

### Step 2: Run Inference
Executes GPT-2-medium and DistilGPT-2 with CodeCarbon tracking.
```bash
python code/run_inference.py --model gpt2-medium
python code/run_inference.py --model distilgpt2
```
*Output*: `data/processed/llm_inference_results.json`

### Step 3: Calculate Emissions
Computes LOC, applies human baseline, and normalizes.
```bash
python code/calculate_emissions.py
```
*Output*: `data/processed/emissions_per_loc.csv`

### Step 4: Analyze & Report
Performs Distribution Overlap Analysis and generates the report.
```bash
python code/analyze_results.py
python code/generate_report.py
```
*Output*: `data/outputs/final_report.md`

## Verification

To verify the pipeline locally:
```bash
pytest tests/
```

## Troubleshooting

- **CodeCarbon Error**: Ensure you are not running in a Docker container without access to host power metrics. On CI, CodeCarbon may use a fallback mode.
- **Memory Error**: If RAM usage exceeds 7GB, reduce the batch size in `run_inference.py`.
- **0 LOC Errors**: Prompts that generate empty code are automatically filtered. Check `data/processed/emissions_per_loc.csv` for excluded records.
