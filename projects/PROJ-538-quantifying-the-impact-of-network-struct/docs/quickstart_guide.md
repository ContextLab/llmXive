# Quick Start Guide

## 1. Setup

Ensure Python 3.11+ is installed.

```bash
pip install -r requirements.txt
```

## 2. Run the Pipeline

Execute the main pipeline:

```bash
python -m code.main
```

## 3. Synthetic Mode

If real data is unavailable, the pipeline automatically switches to synthetic mode. To force synthetic mode:

```bash
python -m code.main --mode synthetic
```

## 4. View Results

Check `data/processed/` for:
- `correlation_report.json`
- `sensitivity_report.csv`
- `power_analysis_report.json`
- `correlation_heatmap.png`

## 5. Run Tests

```bash
pytest tests/ -v
```

## 6. Linting

```bash
python -m code.format_lint_check
```

## Troubleshooting

- **DataUnavailable**: Check network connection or switch to synthetic mode.
- **VoronoiFailure**: Verify input data has periodic box information.
- **ImportError**: Ensure all dependencies are installed.
