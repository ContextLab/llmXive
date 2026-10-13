# Quickstart: The Impact of Bounded Confidence on Opinion Polarization Speed

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- Git
- ~500 MB disk space for data artifacts
- ~7 GB RAM (for batch network generation and simulation)

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
 ```

2. **Create and activate a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline consists of three sequential steps. Run them in order to reproduce the full study. Each step depends on the output of the previous one.

### Step 1: Generate Networks

Generates multiple instances of each topology (ER, BA, WS) with exactly 500 nodes. [UNRESOLVED-CLAIM: c_2358d80f — status=not_enough_info]

```bash
python -m code.generate_networks --topology ER --instances 1 --seed 0
```

**Verification**: This command creates:
- `data/raw/networks/ER_0000.edgelist` (space-separated edge list)
- `data/raw/networks/metadata_ER_0000.json` (network metadata with structural metrics)

To generate the full study ensemble (50 instances per topology) [UNRESOLVED-CLAIM: c_ef747d7f — status=not_enough_info]:
```bash
python -m code.generate_networks --topology ER --instances 50 --seed 0
python -m code.generate_networks --topology BA --instances 50 --seed 0
python -m code.generate_networks --topology WS --instances 50 --seed 0
```

Or generate all topologies at once:
```bash
python -m code.generate_networks --instances 50 --seed 0
```

**Output files**:
- `data/raw/networks/ER_*.edgelist` (150 files for all topologies)
- `data/raw/networks/metadata_*.json` (150 metadata files)
- `data/raw/networks/{ER,BA,WS}_metadata.csv` (summary CSV per topology)

### Step 2: Run Simulations

Executes the Hegselmann-Krause (HK) opinion dynamics model for all networks across a sweep of confidence thresholds (ε values) and multiple random seeds.

```bash
python -m code.run_batch \
 --networks data/raw/networks/ \
 --output data/raw/simulations/ \
 --epsilon-start 0.05 [UNRESOLVED-CLAIM: c_8a4dfe55 — status=not_enough_info] \
 --epsilon-end 0.50 [UNRESOLVED-CLAIM: c_2b83dbef — status=not_enough_info] \
 --epsilon-step 0.05 [UNRESOLVED-CLAIM: c_48977965 — status=not_enough_info] \
 --seeds 50
```

**Parameters**:
- `--networks`: Directory containing edgelist files (output from Step 1)
- `--output`: Directory where HDF5 result files will be written
- `--epsilon-start`: Starting confidence threshold (default: 0.05)
- `--epsilon-end`: Ending confidence threshold (default: 0.50)
- `--epsilon-step`: Step size for ε sweep (default: 0.05)
- `--seeds`: Number of random seeds per (network, ε) pair (default: 50)
- `--max-iter`: Maximum iterations per simulation (default: 10,000)
- `--tol`: Convergence tolerance (default: 1e-4)

**Output files**:
- `data/raw/simulations/run_*.h5` (HDF5 files with opinions and metadata)
- `data/raw/simulations/summary.csv` (aggregated results: 1,500 rows for 3 topologies × 10 ε values × 50 seeds)

**Expected runtime**: ~4-5 hours [UNRESOLVED-CLAIM: c_349dfb1e — status=not_enough_info] on a 2-CPU GitHub Actions runner.

### Step 3: Analyze Results

Fits power-law models to convergence times, detects critical thresholds, and performs regression analysis.

```bash
python -m code.analyze_scaling \
 --simulations data/raw/simulations/ \
 --networks data/raw/networks/ \
 --output data/processed/
```

**Parameters**:
- `--simulations`: Directory containing summary.csv from Step 2
- `--networks`: Directory containing network metadata from Step 1
- `--output`: Directory for processed results (CSVs, JSONs, figures)

**Output files**:
- `data/processed/epsilon_c_values.json` (detected critical thresholds)
- `data/processed/scaling_fits.csv` (power-law fit parameters: γ, R², standard error)
- `data/processed/regression_topology.csv` (Model A: γ ~ topology)
- `data/processed/regression_structural_*.csv` (Model B: γ ~ assortativity + path_length per topology)
- `figures/gamma_vs_assort.png` (scatter plot of γ vs. assortativity)
- `figures/time_vs_epsilon.png` (log-log plot of convergence time vs. ε)
- `data/checksums.json` (SHA-256 hashes of all processed artifacts)

**Expected runtime**: ~5-10 minutes [UNRESOLVED-CLAIM: c_0896b8b8 — status=not_enough_info].

## Full Pipeline in One Command

To run the complete analysis from scratch:

```bash
# Step 1: Generate networks
python -m code.generate_networks --instances 50 --seed 0

# Step 2: Run simulations (takes ~4-5 hours [UNRESOLVED-CLAIM: c_349dfb1e — status=not_enough_info])
python -m code.run_batch \
 --networks data/raw/networks/ \
 --output data/raw/simulations/ \
 --epsilon-start 0.05 [UNRESOLVED-CLAIM: c_8a4dfe55 — status=not_enough_info] \
 --epsilon-end 0.50 [UNRESOLVED-CLAIM: c_2b83dbef — status=not_enough_info] \
 --epsilon-step 0.05 [UNRESOLVED-CLAIM: c_48977965 — status=not_enough_info] \
 --seeds 50

# Step 3: Analyze results
python -m code.analyze_scaling \
 --simulations data/raw/simulations/ \
 --networks data/raw/networks/ \
 --output data/processed/
```

## Verification & Testing

To verify that the installation and logic are correct:

### Run the quick-start verification (Step 1 only)
```bash
python -m code.generate_networks --topology ER --instances 1 --seed 0
ls -lh data/raw/networks/ER_0000.edgelist
ls -lh data/raw/networks/metadata_ER_0000.json
```

Both files should exist and be non-empty.

### Run unit tests
```bash
pytest tests/unit/ -v
```

This runs tests for:
- HK update logic and convergence detection
- Network generation and metrics calculation
- Checksum verification
- Schema validation

### Run integration tests
```bash
pytest tests/integration/ -v
```

This runs end-to-end tests for the full simulation pipeline.

### Run all tests
```bash
pytest -v
```

## Troubleshooting

### Memory errors during network generation
If you encounter `MemoryError` or `OSError` (out of memory), reduce the number of instances:
```bash
python -m code.generate_networks --instances 10 --seed 0
```

The default of 50 instances is calibrated for the 7 GB GitHub Actions limit.

### Simulations timing out
If the batch simulation (Step 2) exceeds the 5-hour budget, reduce the number of seeds or ε values:
```bash
python -m code.run_batch \
 --networks data/raw/networks/ \
 --output data/raw/simulations/ \
 --epsilon-start 0.05 [UNRESOLVED-CLAIM: c_8a4dfe55 — status=not_enough_info] \
 --epsilon-end 0.50 [UNRESOLVED-CLAIM: c_2b83dbef — status=not_enough_info] \
 --epsilon-step 0.05 [UNRESOLVED-CLAIM: c_48977965 — status=not_enough_info] \
 --seeds 25 # Reduced from 50
```

### Non-convergent simulations
If more than 10% of runs report `status: "non_converged"`, check if:
- ε is too low (below the critical threshold ε_c for that network)
- `--max-iter` is too small relative to the convergence speed
- The network is disconnected (should be handled automatically)

### Missing output files
After running Step 3, verify that the expected files exist:
```bash
ls -lh data/processed/epsilon_c_values.json
ls -lh data/processed/scaling_fits.csv
ls -lh figures/gamma_vs_assort.png
ls -lh figures/time_vs_epsilon.png
```

If any are missing, check the script output for error messages.

## Performance Expectations

| Step | Typical Runtime | RAM Usage | Disk Output |
|------|-----------------|-----------|-------------|
| 1. Generate networks (50 × 3 topologies) | ~1 minute | ~500 MB | ~50 MB |
| 2. Run simulations (1,500 runs) | ~4-5 hours [UNRESOLVED-CLAIM: c_349dfb1e — status=not_enough_info] | ~2-3 GB | ~200 MB |
| 3. Analyze results | ~5-10 minutes [UNRESOLVED-CLAIM: c_0896b8b8 — status=not_enough_info] | ~1 GB | ~10 MB |
| **Total** | **~4.5-5.5 hours [UNRESOLVED-CLAIM: c_d1728eb8 — status=not_enough_info]** | **~3-4 GB peak [UNRESOLVED-CLAIM: c_d8906e09 — status=not_enough_info]** | **~260 MB** |

All measurements assume a 2-CPU GitHub Actions runner with 7 GB RAM.

## Next Steps

After the pipeline completes successfully:

1. **Review the figures** in `figures/` to visualize the scaling relationships
2. **Examine the regression results** in `data/processed/regression_*.csv` to identify significant predictors
3. **Check the sensitivity analysis** (run `code/run_sensitivity.py`) to confirm robustness
4. **Read the writeup** in `docs/methods_results.md` for a summary of findings

## Citation

If you use this pipeline, please cite:

```bibtex
@software{bounded_confidence_2026,
 title={The Impact of Bounded Confidence on Opinion Polarization Speed},
 author={Your Name},
 year={2026},
 url={
}
```

## Support

For issues, questions, or suggestions, please:
- Open a GitHub issue
- Check the `docs/` folder for detailed methodology notes
- Review test output with `pytest -v` for debugging

---

**Last updated**: 2026-07-13
**Specification**: `specs/001-the-impact-of-bounded-confidence-on-opin/spec.md`
**Plan**: `specs/001-the-impact-of-bounded-confidence-on-opin/plan.md`
