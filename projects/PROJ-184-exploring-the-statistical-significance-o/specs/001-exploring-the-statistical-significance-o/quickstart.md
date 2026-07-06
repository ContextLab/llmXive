# Quickstart: Exploring the Statistical Significance of Fine‑Structure Constant Variations

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions account (for CI) or local Python environment

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/proj-184-fine-structure-constant.git
   cd proj-184-fine-structure-constant
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Quick Run (Benchmark with Simulated Data)

To verify the pipeline works on free-tier hardware:

```bash
# Run the benchmark (simulated absorbers)
python code/analysis/run_analysis.py --mode benchmark

# Expected output:
# - Posterior samples saved to data/results/posterior_samples.nc
# - Bayes factors saved to data/results/bayes_factors.csv
# - Corner plots saved to data/results/plots/
# - Log: "Benchmark complete. 95% CI recovery: 96% (target: ≥95%)"
```

## Running with Real Data (ESO UVES)

> **Note**: Requires ESO API key and internet access. If ESO is unavailable, the pipeline will skip real data and run on simulated data only.

1. **Set up ESO API key**:
   ```bash
   export ESO_API_KEY="your_api_key_here"
   ```

2. **Run with real data**:
   ```bash
   python code/analysis/run_analysis.py --mode production --quasar-list data/inputs/quasar_ids.txt
   ```

3. **Monitor progress**:
   - Check `code/logs/run_20260627.log` for progress.
   - If R-hat >1.01, the script will re-run with increased warmup.

## Testing

Run unit and integration tests:

```bash
pytest code/tests/ -v --cov=code
```

**Key Tests**:
- `test_hierarchical_model.py`: Verifies 95% CI recovery on simulated data (SC-001).
- `test_model_comparison.py`: Verifies Bayes factor accuracy (SC-002).
- `test_schemas.py`: Validates data against YAML schemas (contracts/).

## Output Files

After a successful run:

- `data/results/posterior_samples.nc`: Full posterior samples.
- `data/results/bayes_factors.csv`: Model comparison results.
- `data/results/plots/`: Corner plots, trace plots.
- `code/logs/run_YYYYMMDD.log`: Detailed execution log.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **ESO API rate-limited** | Wait 1 minute; re-run. Pipeline has built-in retry. |
| **NUTS non-convergence** | Check `code/logs/run_YYYYMMDD.log` for R-hat values. Increase warmup in `config.py`. |
| **Memory error** | Reduce number of absorbers or draws in `config.py`. |
| **Missing NIST transition** | Log warning; skip transition. Do not include in analysis. |

## Next Steps

1. Review `research.md` for statistical methodology.
2. Examine `data-model.md` for data structures.
3. Run `pytest` to validate all components.
4. Check `contracts/` for schema validation.
