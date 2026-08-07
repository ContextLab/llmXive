# Quickstart Guide: llmXive Follow-up

## Prerequisites
- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

## Project Structure
- `code/`: Source code
- `data/`: Raw, curated, and results data
- `specs/`: Design documents and contracts
- `tests/`: Test suites

## Execution

### 1. Create Project Structure
```bash
python code/setup_project_structure.py
```

### 2. Download Data
```bash
python code/data/download.py
```

### 3. Derive Ground Truth
```bash
python code/data/derive_gt.py
```

### 4. Filter Hard Subset
```bash
python code/data/filter_hard.py
```

### 5. Generate Synthetic Issues
```bash
python code/data/curate.py
```

### 6. Validate Hard Subset
```bash
python code/data/validate_hard.py
```

### 7. Run Full Pipeline
```bash
python code/main.py
```

### 8. Generate Metrics
```bash
python code/analysis/generate_final_metrics.py
```

### 9. Generate Plots
```bash
python code/analysis/plots.py --input data/results/final_metrics.json --output docs/figures/
```

### 10. Generate Report
```bash
python code/analysis/report_generator.py
```

## Note
- Ensure `data/raw/bench.final.public.jsonl` exists before running `derive_gt.py`.
- The `--mode full` argument has been removed from `main.py` to align with the current implementation. Run `python code/main.py` directly.