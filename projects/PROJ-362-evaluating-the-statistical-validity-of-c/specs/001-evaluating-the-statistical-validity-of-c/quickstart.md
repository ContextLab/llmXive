# Quickstart: Evaluating the Statistical Validity of Common Ranking Metrics

## Prerequisites

- Python 3.10+
- 7GB+ RAM available
- Internet access (for dataset download)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-362-evaluating-the-statistical-validity-of-c/code/
   pip install -r requirements.txt
   ```

2. **Verify Environment**:
   ```bash
   python -c "import numpy, pandas, scipy, datasets; print('CPU-only environment ready')"
   ```

## Execution

Run the full analysis pipeline:

```bash
python main.py
```

**Flags (Optional)**:
- `--subsample 100`: Force subsampling to 100 queries (useful for testing).
- `--max-permutations 1000`: Limit permutation count for speed.
- `--skip-download`: Assume data is already in `data/raw/`.

## Output Artifacts

Upon completion, the following files will be generated in `results/`:

- `p_values.csv`: Raw and corrected p-values, observed scores, MDES, and power for all queries.
- `mdes_summary.csv`: Minimum Detectable Effect Size estimates (noise sigma and metric delta).
- `plots/ndcg_density.png`: Density plot of observed vs. null NDCG with MDES annotation.
- `plots/map_density.png`: Density plot of observed vs. null MAP with MDES annotation.

## Troubleshooting

- **Memory Error**: If the script fails due to memory, reduce `--subsample` or `--max-permutations`.
- **Network Error**: The system automatically retries up to 3 times. If it fails, check internet connectivity.
- **Missing Data**: Ensure `data/raw/` contains the downloaded qrels. Re-run with `--force-download`.
