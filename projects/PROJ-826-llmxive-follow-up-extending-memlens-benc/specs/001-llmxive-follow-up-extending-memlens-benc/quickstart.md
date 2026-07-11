# Quickstart: llmXive follow-up: extending "MemLens"

## Prerequisites
- Python 3.11+
- Git
- GitHub Actions Runner (or local machine with sufficient RAM, CPU-only)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-826-llmxive-follow-up-extending-memlens-benc
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: Ensure `faiss-cpu` is installed, not `faiss-gpu`.*

## Running the Pipeline

### 1. Download Data
The pipeline will automatically download the MemLens dataset on first run if `data/raw/` is empty.
```bash
python code/data_loader.py --download
```
*Note: This step includes retry logic for image assets. Failed downloads are logged and the query is excluded.*

### 2. Run Evaluation (Full)
Executes the full pipeline: download, store construction, retrieval, generation, and statistical analysis.
```bash
python code/run_pipeline.py --full
```
*This may take several hours. It will save intermediate checkpoints (appends to `outputs/results.csv`).*

### 3. Run Evaluation (Debug/Quick)
Runs on a small subset (e.g., 5 queries) to verify the pipeline logic.
```bash
python code/run_pipeline.py --debug
```

### 4. View Results
Results are saved to `outputs/results.csv` and `outputs/statistics.json`.
```bash
cat outputs/statistics.json
```

## Troubleshooting
- **OOM Error**: Reduce the `batch_size` in `code/config.py` or use the `--debug` flag.
- **CUDA Error**: Ensure `device="cpu"` is set in `code/generator.py`.
- **Missing Dataset**: Check that the HuggingFace URLs in `research.md` are accessible.
- **Timeout**: If the job times out, `outputs/results.csv` will contain partial results valid for analysis.