# Quickstart: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Prerequisites

- Python 3.11+
- Git
- Access to the Z-Reward dataset (or open substitute)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download data**:
   - If using Z-Reward, place the dataset files in `data/raw/`.
   - If using a public dataset, follow the download instructions in `research.md`.

## Running the Pipeline

1. **Ingest Data**:
   ```bash
   python code/ingestion.py
   ```

2. **Compute Features**:
   ```bash
   python code/features.py
   ```

3. **Train Model**:
   ```bash
   python code/train.py
   ```

4. **Validate Results**:
   ```bash
   python code/stats.py
   ```

5. **View Results**:
   - Check `results/results.json` for metrics.
   - Check `results/model.pkl` for the trained model.
   - Check `data/processed/data_quality_report.json` for exclusion logs.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Troubleshooting

- **Missing Data**: Check `data/raw/` for required files.
- **Memory Error**: Reduce dataset size or use streaming.
- **Import Error**: Ensure virtual environment is activated and dependencies are installed.