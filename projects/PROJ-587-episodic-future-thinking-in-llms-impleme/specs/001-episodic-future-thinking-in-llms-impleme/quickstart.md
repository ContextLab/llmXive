# Quickstart: Episodic Future Thinking

## 1. Prerequisites

- Python 3.11+
- 7GB+ RAM
- 14GB+ Disk Space
- Git

## 2. Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code
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

## 3. Data Download

Run the data download script to fetch ALFWorld and TextWorld datasets. This step ensures data is checksummed and stored in `data/raw/`.

```bash
python src/utils/loaders.py --fetch
```

*Note: This script uses the verified URLs from `research.md` and records checksums in `state/`.*

## 4. Configuration

Ensure `config.yaml` exists in the `code/` directory. If missing, run:

```bash
python src/utils/init_config.py
```

This creates `config.yaml` with default log levels and the fixed cosine threshold (0.75).

## 5. Running the Experiment

### 5.1 Build Episodic Memory
```bash
python src/episodic_memory/store.py --build
```
This extracts trajectories, generates embeddings, and builds the FAISS HNSW index.

### 5.2 Run Baseline & Episodic Models
```bash
python src/planning/generator.py --mode baseline --tasks 50
python src/planning/generator.py --mode episodic --tasks 50
```

### 5.3 Sensitivity Sweep (FR-006)
```bash
python src/evaluation/sensitivity.py --thresholds 0.70 0.75 0.80
```

### 5.4 Evaluation & Analysis
```bash
python src/evaluation/accuracy.py --mixed-effects
python src/evaluation/confidence.py --counterfactual
```

## 6. Verification

To verify the results:
1. Check `data/results/evaluation_results.jsonl` for accuracy metrics.
2. Verify `data/processed/index.faiss` exists and is non-empty.
3. Run `pytest tests/` to ensure all contract tests pass.

## 7. Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in dataset loading. Reduce batch size in `config.yaml`.
- **Retrieval Timeout**: Check FAISS index configuration; ensure HNSW is used, not brute-force.
- **Missing Config**: Run `src/utils/init_config.py` to generate `config.yaml`.
