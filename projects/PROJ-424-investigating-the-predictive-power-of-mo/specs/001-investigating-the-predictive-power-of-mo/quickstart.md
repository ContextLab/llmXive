# Quickstart: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Prerequisites

- Python 3.11+
- GROMACS 2023+ (or LAMMPS)
- `git`
- GitHub Actions runner (for CI execution)

## Installation

```bash
# Clone repository
git clone
cd projects/PROJ-424-investigating-the-predictive-power-of-mo

# Create virtual environment
python -m venv venv
source venv/bin/activate # Linux/Mac
# or: venv\Scripts\activate # Windows

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration

1. **Edit `code/config.py`**:
 - Set `SOLVENTS = ["water", "ethanol", "acetone"]`
 - Set `TIMESCALES = [1.0, 5.0, 10.0]`
 - Set `FORCE_FIELD = "martini3"`

2. **Verify NIST references**:
 - Check `data/raw/nist_refs.json` for expected values.
 - Update if necessary (with checksum).

3. **Prepare topologies**:
 - Ensure `data/raw/topologies/` contains `.gro` and `.top` files for each solvent.

## Running the Pipeline

### Full Batch Analysis

```bash
python code/main.py --full-batch
```

This executes:
- 9 simulations (3 solvents × 3 timescales)
- MSD extraction & diffusion calculation
- Bootstrap resampling (1000 iters)
- Sensitivity analysis
- Report generation

### Single Run (Testing)

```bash
python code/main.py --solvent water --timescale 1.0
```

### Sensitivity Analysis Only

```bash
python code/main.py --sensitivity --solvent ethanol --timescale 10.0
```

## Output

- **Plots**: `data/processed/timescale_accuracy_plot.png`
- **Tables**: `data/processed/summary_table.csv`
- **Logs**: `data/interim/simulation_logs/`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Simulation fails to equilibrate | Check `R^2` in logs; reduce system size |
| Bootstrap exceeds time limit | Fallback to 100 iterations (automatic) |
| NIST data missing | Manually edit `data/raw/nist_refs.json` |
| Memory error | Reduce system size or timescale |

## Verification

Run unit tests:

```bash
pytest tests/unit/
```

Run integration tests:

```bash
pytest tests/integration/
```
