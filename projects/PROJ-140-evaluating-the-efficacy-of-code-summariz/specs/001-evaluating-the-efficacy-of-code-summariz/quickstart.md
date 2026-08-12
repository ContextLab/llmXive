# Quickstart: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Prerequisites
- Python 3.11+
- Git
- (Optional) CUDA-enabled GPU for LLM inference (for `--mode=real` only)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd <repo-dir>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Setup

### 3.1 Download Defects4J
Run the download script to fetch and verify the dataset:
```bash
python code/download.py --source "huggingface" --dataset "chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3"
```
This will save the dataset to `data/raw/defects4j.parquet` and record the checksum.

### 3.2 Generate Summaries (Simulation Mode)
For CI and testing, use simulated summaries:
```bash
python code/summarize.py --mode sim
```
This generates mock LLM and rule-based summaries for testing the pipeline.

### 3.3 Generate Summaries (Real Mode - GPU Required)
**Note**: This step requires a GPU. Run on a machine with CUDA or use the provided Kaggle notebook.
```bash
python code/summarize.py --mode real --device cuda --quantize 8bit
```
*If run on CPU, this will fail with a clear error message directing you to the GPU escape hatch.*

## 4. Running the Study

### 4.1 Simulate Participant Interactions (CI Test)
```bash
python code/simulate_study.py --participants 12 --tasks-per-condition 10 --seed 42
```
Output: `data/interaction_logs/anonymized_logs.csv`.

### 4.2 Run Statistical Analysis
```bash
python code/analysis.py --input data/interaction_logs/anonymized_logs.csv --mode ci
```
Output: `data/analysis_results.json` containing p-values, effect sizes, and CIs.

## 5. Verification

### 5.1 Run Tests
```bash
pytest tests/ -v --cov=code
```

### 5.2 Reproducibility Check
Run the CI workflow locally to verify reproducibility:
```bash
# Simulate the CI environment
docker run --rm -v $(pwd):/work -w /work python:3.11 bash -c "pip install -r requirements.txt && pytest tests/integration/test_pipeline.py"
```

## 6. Troubleshooting

- **LLM Timeout**: If LLM generation times out, the system automatically falls back to rule-based summaries. Check `data/processed/summaries_llm.csv` for `generation_status=fallback`.
- **Memory Error**: If RAM is exceeded, enable streaming in `download.py` (`streaming=True`).
- **GPU Not Found**: If running `--mode=real` without a GPU, the script will exit. Use the Kaggle GPU notebook for real LLM inference.
