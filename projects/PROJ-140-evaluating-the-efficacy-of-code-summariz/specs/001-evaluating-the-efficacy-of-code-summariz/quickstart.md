# Quickstart: Evaluating Code Summarization Techniques for Bug Localization

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)
- `srcml` system package (for rule-based summary generation)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-140-evaluating-the-efficacy-of-code-summariz
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

## Data Preparation

### Step 0: Latency Calibration (Required)
Before starting the study, verify timestamp precision:
```bash
python code/utils/latency_calibrator.py
```
This must return `PASS` (≤100ms) before proceeding.

### Step 1: Download Defects4J
Run the data preparation script to fetch the dataset:
```bash
python code/data_prep/download_defects4j.py
```
This will download the Parquet files from the verified HuggingFace URLs and save them to `data/defects4j/`. It will also verify that `source_code` and `ground_truth_line` columns exist.

### Step 2: Generate Summaries
To generate summaries (uses deterministic LLM-Sim for CPU/Ci, srcML for rule-based):
```bash
# For CPU-only testing (generates deterministic LLM-Sim summaries)
python code/data_prep/generate_summaries.py --mode llm_sim

# For real LLM generation (requires GPU/CUDA - not recommended for CI)
# python code/data_prep/generate_summaries.py --mode real_llm --model codellama/CodeLlama-7b-hf
```
*Note*: The `llm_sim` mode is deterministic and reproducible without GPU.

## Running the Analysis

Execute the statistical analysis pipeline:
```bash
python code/analysis/run_statistics.py --data data/interaction_logs/anonymized_logs.csv --summaries data/summaries/
```

**Output**: Results are saved to `data/analysis_results/results.csv`.

## Reproducibility Check (CI)

To verify the reproducibility constraint (≤6h, CPU-only) and resource limits:
```bash
# This simulates the GitHub Actions free-tier runner
python code/analysis/run_statistics.py --data data/interaction_logs/anonymized_logs.csv --summaries data/summaries/ --ci-mode
```
This mode enforces strict memory and time limits and uses fixed random seeds.

## Resource Monitoring

To manually check resource usage:
```bash
python code/utils/resource_monitor.py --script code/analysis/run_statistics.py
```

## Versioning

To generate and record artifact hashes:
```bash
python code/utils/hash_artifacts.py
```
This writes hashes to `state/projects/PROJ-140.../artifact_hashes.yaml`.

## Testing

Run the unit tests:
```bash
pytest tests/
```
