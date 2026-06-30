# Quickstart: ShutterMuse

## Prerequisites
- Python 3.11+
- Git
- API Keys for GPT‑4V (if using the cloud model)
- 14 GB Disk Space
- 7 GB RAM

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-789-shuttermuse-capture-time-photography-gui/code/
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins CPU‑only versions of PyTorch, Transformers, and `deepface==0.0.83` (the sole source for FairFace weights).*

4. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export HF_TOKEN="your-huggingface-token"
   ```

## Running the Pipeline

### 1. Download Data (Sampled)
```bash
python src/download.py --sample-size
```
Downloads a balanced subset of AVA and COCO images (≈ 30 per model) and verifies checksums.

### 2. Run Inference & Categorization
```bash
python src/main.py --mode full --models llava qwen gpt4
```
This executes:
- Face detection and demographic inference (FairFace) with confidence ≥ 0.85.
- MLLM prompting (standard + counterfactual) with exponential‑backoff retries.
- Error categorization, including the “Potential Reasoning Error (hypothesis)” label.

*Note: On a CPU‑only runner this step typically takes 1–4 hours.*

### 3. Run Analysis
```bash
python src/analysis.py
```
Generates statistical tests (Chi‑square, Fisher’s Exact, or Monte‑Carlo chi‑square as appropriate) and writes results to `data/processed/analysis_results.csv`. Effect sizes with bootstrap confidence intervals are included.

### 4. Generate Report
```bash
python src/report.py
```
Outputs `results/report.md` with comparative tables, effect sizes, methodological notes, and explicit discussion of limitations.

### 5. Validate Contracts & State
```bash
python src/validate_contracts.py
python src/state_update.py
```
Ensures all CSV/JSON outputs conform to the schemas in `contracts/` and records artifact hashes in `state/project_state.yaml`.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration test (small subset):
```bash
pytest tests/integration/test_full_pipeline.py --sample-size 10
```

## Troubleshooting
- **Memory Error:** Reduce `--sample-size` in `download.py`.  
- **API Rate Limit:** The script automatically retries. If it fails, wait 5 minutes and re‑run.  
- **Demographic Inference Fails:** Ensure `deepface` weights are installed. Check `data/processed/demographics.csv` for confidence scores < 0.85; those rows are excluded from bias analysis but retained for error logging.  
