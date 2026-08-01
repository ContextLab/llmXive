# Quickstart: llmXive Feature Distillation

## 1. Setup Environment
```bash
python code/scripts/setup_environment.py
```

## 2. Fetch Data
```bash
python code/scripts/run_pipeline.py --stage fetch
```

## 3. Run Full Pipeline
```bash
python code/scripts/run_pipeline.py
```

## 4. Verify Outputs
Check the following files:
- `data/results/correlation_results.csv`
- `reports/feasibility_profile.json`
- `data/sensitivity_matrix_full.csv`

## 5. Run Tests
```bash
pytest code/tests/ -v
```

## Notes
- Ensure you have sufficient disk space (~10GB).
- The pipeline is CPU-only and optimized for < 7GB RAM.
- Gates (T040, T041, T021) must pass for the pipeline to complete successfully.