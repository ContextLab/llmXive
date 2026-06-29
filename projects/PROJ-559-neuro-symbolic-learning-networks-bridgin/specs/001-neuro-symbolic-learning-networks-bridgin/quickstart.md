# Quickstart: Neuro‑Symbolic Learning Networks

## Prerequisites

- Python 3.11+
- Git
- GitHub account (for CI workflow)
- IRB approval for human participant data collection (FR-010, FR-011)

## Quick Start (5 Minutes)

### Step 1: Clone and Setup

```bash
git clone <repo-url>
cd projects/PROJ-559-neuro-symbolic-learning-networks-bridgin
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

### Step 2: Download Datasets

```bash
python code/download/fetch_datasets.py
```

This will:
- Download ASSISTments datasets from verified HuggingFace URLs
- Checksum all files and store in `data/raw/`
- Abort with clear error message if download exceeds 300 seconds (SC-008)

### Step 3: Generate Explanations (Sample Run)

```bash
python code/generate/explanation_generator.py --problem-id sample_001 --mode all
```

This produces three files:
- `data/derived/explanation_neural.txt`
- `data/derived/explanation_symbolic.txt`
- `data/derived/explanation_neuro_symbolic.txt`

### Step 4: Run Calibration (If Human Pilot Data Available)

```bash
python code/simulate/calibration.py --pilot-data data/pilot/human_calibration.csv
```

Output: Calibration statistics (RMSE, t‑test p‑value). If calibration fails (RMSE >0.15 or p <0.10), iterate BKT parameters.

### Step 5: Run Full Simulation

```bash
python code/simulate/run_simulation.py --num-students 2000 --conditions neural,symbolic,neuro_symbolic
```

Output: `data/derived/simulation_logs.csv` with ≥6,000 records.

### Step 6: Run Analysis

```bash
python code/analyze/mixed_effects.py --input data/derived/simulation_logs.csv --output data/derived/regression_results.json
```

Output: Regression table, effect sizes with 95% CI.

## CI Workflow

The GitHub Actions workflow (`.github/workflows/ci.yml`) executes:

1. **Download datasets** (timeout: 300s)
2. **Generate explanations** (sample: 200 problems)
3. **Run simulation** (2,000 students per condition)
4. **Run analysis** (mixed‑effects regression)
5. **Resource monitoring** (SC-006: report CPU ≤2 cores, memory ≤7 GB)
6. **Contract validation** (validate `data/derived/*.csv` against `contracts/*.schema.yaml`)

## Validation

### Contract Tests

```bash
pytest tests/contract/test_schemas.py
```

Validates that all generated data files conform to the YAML schemas in `contracts/`.

### Integration Tests

```bash
pytest tests/integration/test_pipeline.py
```

End‑to‑end pipeline test on a single problem.

### Unit Tests

```bash
pytest tests/unit/test_bkt.py
```

BKT simulator unit tests.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dataset download timeout | Check network; verify HuggingFace URL reachability; raise timeout if needed (document in config.py) |
| Memory exceeds 7 GB | Subset data; enable streaming processing; reduce sample size |
| LLM inference too slow | Use smaller model; reduce problem sample; document trade‑off |
| Calibration fails | Iterate BKT parameters; verify human pilot data quality |
| Regression fails | Check data completeness; verify no missing coefficients; increase sample size |

## Notes

- **Human Data Collection**: FR-010 and FR-011 require human participant data (≥50 for calibration, ≥200 for final analysis). This must be collected via IRB‑approved study before simulation can proceed for full validity.
- **Khan Academy Gap**: The spec references Khan Academy but no verified source exists. The plan proceeds with ASSISTments only; this limits generalizability.
- **Compute Constraints**: All methods are CPU‑only; no GPU/CUDA. If runtime exceeds 6h, reduce sample size or problem count.
