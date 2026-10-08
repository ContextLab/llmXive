# Quickstart Guide: Residue Distribution of Euler's Totient Function

This guide validates the reproducibility of the analysis pipeline.

## Prerequisites

1. Ensure you have Python 3.9+ installed.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution

To run the full analysis for a large range (e.g., N=5,000,000), execute:

```bash
python code/run_analysis.py --n 5000000 --primes 3,5,7,11
```

### Validation Mode

To quickly validate the pipeline in a fresh environment (recommended for CI), run:

```bash
python code/validate_quickstart.py
```

This script:
1. Verifies directory structure (`data/`, `results/`, `code/`).
2. Executes the pipeline with a small `N` (default 10,000) to ensure all stages (Sieve, Stats, Visualization) run without error.
3. Validates that output JSON files conform to the expected schema.
4. Returns exit code 0 on success, 1 on failure.

## Output Artifacts

Upon successful execution, the following files will be generated:

- `data/raw/residues_{prime}_{N}.json`: Raw residue counts.
- `data/processed/stats_{prime}_{N}.json`: Statistical test results (Chi-squared, Block Bootstrap).
- `results/plots/`: Generated visualizations (bar plots, QQ-plots).
- `results/reports/summary_{N}.md`: Summary report with pass/fail flags.

## Troubleshooting

- **Memory Limit**: If the process fails due to memory, increase `--memory-limit-mb` or reduce `--n`.
- **Missing Constants**: Ensure `data/constants.yaml` exists and contains valid numeric values for error bounds.
- **Benchmark Failure**: If the benchmark exceeds 1 hour for N=5M, check system resources or review `results/reports/benchmark_status.json`.