# Quickstart: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities

## Prerequisites

- Python 3.11+
- Git
- 16GB RAM (recommended for local dev, 7GB required for CI)
- Access to HuggingFace Hub (for datasets and models)

## Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-282-evaluating-the-effectiveness-of-llms-for
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import torch; import transformers; import datasets; print('OK')"
   ```

## Data Download

The pipeline automatically downloads datasets from verified sources on first run.
```bash
# Run the download script
python src/data/download.py
```
*Output*: `data/raw/vuldeepecker.parquet`, `data/raw/nist_juliet.jsonl`, `data/raw/jsvulndb.parquet`.

## Running the Pipeline

Execute the full pipeline (Download -> Features -> Inference -> Analysis):
```bash
python src/main.py --config config/default.yaml
```

### Specific Steps

1. **Feature Extraction Only**
   ```bash
   python src/data/feature_extractor.py --input data/raw/ --output data/processed/features.parquet
   ```

2. **LLM Inference Only**
   ```bash
   python src/models/llm_inference.py --input data/processed/features.parquet --output data/processed/predictions_llm.parquet
   ```

3. **Statistical Analysis Only**
   ```bash
   python src/analysis/regression.py --input data/processed/analysis_dataset.parquet --output data/processed/metrics.json
   ```

## Verification

Check that all required artifacts exist:
```bash
# Verify logs
ls data/logs/orchestration_log.json
ls data/logs/linting_config.json

# Verify results
ls data/processed/metrics.json
ls data/processed/sensitivity_analysis.json
```

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `config/default.yaml` to 1.
- **Model Load Fail**: Ensure `HF_HOME` is set and internet is available for initial download.
- **Dataset Missing**: Check `data/raw` for checksums. Re-run `download.py`.