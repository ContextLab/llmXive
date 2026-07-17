# Quickstart Guide

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`
- `python -m spacy download en_core_web_sm`

## Setup
1. Create project structure:
 ```bash
 python -m code.utils.setup_directories
 ```
2. Record dataset checksums:
 ```bash
 python -m code.pipelines.record_checksums
 ```

## Feature Extraction
Run the feature extraction pipeline:
```bash
python -m code.pipelines.extract_features
```

## Correlation Analysis
Run the correlation analysis pipeline:
```bash
python -m code.pipelines.analyze_correlations
```

## Testing
Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```
