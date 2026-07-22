# Quickstart: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## 1. Prerequisites
- Python 3.11+
- Git
- Access to Hugging Face datasets (public)
- GitHub Actions runner (or local equivalent with 7GB+ RAM)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-593-the-binding-problem-in-llms-implementing

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download
The data is downloaded automatically during the first run. For manual download:

```bash
python src/data/download_meg.py
python src/data/download_clutrr.py
```

## 4. Running the Pipeline

### 4.1 Full Pipeline
```bash
python src/main.py --config config/default.yaml
```

### 4.2 Specific Tasks
- **Spectral Analysis**: `python src/analysis/spectral.py --input data/raw/activations.npy`
- **PLV Calculation**: `python src/analysis/plv.py --model-activations data/processed/activations.npy --meg-reference data/raw/meg.parquet`
- **Benchmark Evaluation**: `python src/benchmarks/clutrr_eval.py --seed 42`

## 5. Verification

### 5.1 Unit Tests
```bash
pytest tests/unit/
```

### 5.2 Integration Tests
```bash
pytest tests/integration/
```

### 5.3 Contract Tests
```bash
pytest tests/contract/
```

## 6. Expected Output
- `data/final/results_summary.json`: Aggregated metrics.
- `data/final/statistical_report.json`: Statistical significance results.
- `plots/`: Figures showing spectral peaks and PLV distributions.

## 7. Troubleshooting

- **OOM Error**: Reduce batch size or stream data more aggressively.
- **CUDA Error**: The system will automatically switch to CPU or scale down for Kaggle GPU.
- **Data Missing**: Verify Hugging Face access and network connectivity.
