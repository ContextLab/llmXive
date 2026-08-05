# Quickstart: llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face (for dataset download)
- GB+ RAM available

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben
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

## Running the Experiment

### Step 1: Data Preparation
Download and filter the dataset to retain only high-complexity instances (>500 lines).
```bash
python code/data/loader.py --filter-min-lines 500 --output data/filtered_swe_bench.parquet
```
*Expected Output*: `data/filtered_swe_bench.parquet` containing only valid instances.

### Step 2: Baseline Execution (1B Model)
Run the naive baseline with the 1B model.
```bash
python code/experiments/run_baseline.py --model 1b --strategy baseline --max-instances a sufficient number of instances to ensure statistical power
```
*Note*: Use `--max-instances` to test a subset before full run.

### Step 3: High-Fidelity Execution (1B & 7B Models)
Run the full matrix of strategies.
```bash
python code/experiments/run_high_fidelity.py --models b,7b --strategies baseline,tfidf,diff_aware,summarization --output data/results.csv
```
*Note*: This step includes the A large-scale language model with Q4_K_M quantization. Ensure sufficient RAM.

### Step 4: Statistical Analysis
Run the GLM to test for interaction effects.
```bash
python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json
```

## Verifying Results

1. Check `data/results.csv` for `pass_status` and `failure_mode` columns.
2. Inspect `data/glm_results.json` for the interaction term p-value.
3. Validate that the number of filtered instances is ≥ 50 per cell.

## Troubleshooting

- **Memory Error**: If the 7B model fails to load, ensure `load_in_4bit=True` is set in `config.py`. The script should auto-fallback to "resource_constraint" flag.
- **Timeout**: If an instance exceeds a substantial duration, it is automatically killed and logged. Check `logs/timeout.log`.
- **Dataset Not Found**: Ensure you have internet access to download from Hugging Face.
