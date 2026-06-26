# Quickstart: Social Memory Networks: Modeling Collective Remembering in Multi‑Agent LLMs

## Prerequisites

- Python 3.11+
- pip package manager
- Sufficient RAM available
- Substantial disk space
- Internet connection (for dataset downloads)

## Installation

```bash
# Navigate to project code directory
cd projects/PROJ-586-social-memory-networks-modeling-collecti/code/

# Create isolated virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running Experiments

### Full-Context Baseline (US-1)

```bash
python run_experiment.py --context full --agents 5 --games 1000
```

**Output**: `results/results_full.csv` containing `specialization_index` and `retrieval_efficiency` per game.

### Limited-Context Condition (US-2)

```bash
python run_experiment.py --context limited --agents 5 --games 1000
```

**Output**: `results/results_limited.csv` with same metrics.

### Scaling Analysis (US-3)

```bash
python run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling
```

**Output**: `results/scaling_plot.pdf` with fitted power-law curves and 95% CI.

### Sensitivity Analysis (FR-008)

```bash
python run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512
```

**Output**: Trend report across token thresholds.

## Verification

### Check Dataset Downloads

```bash
python -c "from data.loaders import verify_datasets; verify_datasets()"
```

Expected: All verified URLs accessible; checksums match.

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

Expected: All schema validations pass (game-result, memory-action, analysis-output).

### Reproducibility Check

```bash
# Run twice with same seed
python run_experiment.py --context full --agents 5 --games 100 --seed 42
python run_experiment.py --context full --agents 5 --games 100 --seed 42

# Compare outputs (should be identical)
diff results/run1/results_full.csv results/run2/results_full.csv
```

Expected: No differences (seed=42 guarantees reproducibility per Constitution Principle I).

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `MemoryError` | Dataset too large for RAM | Sample to a representative subset of rows; check `data/derived/` size |
| `CUDA not available` | GPU code attempted | Ensure `transformers` uses CPU; no `device_map="cuda"` |
| `Dataset not found` | Verified URL unreachable | Check internet; use synthetic generator fallback (FR-011) |
| `Schema validation failed` | Output CSV malformed | Check `contracts/` schemas; ensure column names match |

## Output Locations

| Output | Path | Description |
|--------|------|-------------|
| Full-context results | `results/results_full.csv` | US-1 baseline metrics |
| Limited-context results | `results/results_limited.csv` | US-2 comparison metrics |
| Scaling plot | `results/scaling_plot.pdf` | US-3 power-law analysis |
| ANOVA table | `results/anova_output.json` | FR-006 interaction p-value |
| Power analysis | `results/power_analysis_report.md` | FR-009 power estimate |
| Error log | `data/logs/experiment.log` | FR-010 runtime errors |
