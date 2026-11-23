# Quickstart: Evaluating the Statistical Validity of Common Ranking Metrics

## Prerequisites

- Python 3.10+
- Git
- 7 GB RAM, 2 CPU cores (GitHub Actions free-tier compatible)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd llmXive/projects/PROJ-362-evaluating-the-statistical-validity-of-c
   ```

2. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Analysis

### Full Run (with subsampling fallback)
```bash
python code/main.py --collection trec-robust04 --permutations 1000
```

### Specific Dataset
```bash
python code/main.py --collection trec-web-2009 --permutations 1000
```

### Arguments
- `--collection`: TREC dataset name (e.g., `trec-robust04`, `trec-web-2009`).
- `--permutations`: Number of permutations per query (default: 1000).
- `--seed`: Random seed for reproducibility (default: 42).
- `--max-queries`: Maximum queries to process (default: all, with subsampling trigger).

## Output

Results are saved to `results/`:
- `null_distributions/`: CSV files with null scores.
- `p_values.csv`: Raw and corrected p-values.
- `mdes_results.csv`: Minimum Detectable Effect Size.
- `alpha_sweep.csv`: Sensitivity analysis.
- `results_summary.csv`: Final summary table including a "Statistical Interpretation" note.
- `plots/`: Density plots (PNG).

**Statistical Interpretation**: The `results_summary.csv` and any generated report will include an explicit note: *"These findings represent statistical association between the metric score and relevance judgments. They do not imply causal algorithmic improvement."* (Satisfies FR-008).

## Verification

1. Checksums in `state/projects/PROJ-362-evaluating-the-statistical-validity-of-c.yaml` match raw data.
2. All CSVs have required headers (see `contracts/`).
3. `subsample_log.csv` exists if subsampling occurred, recording dropped queries and reasons (Satisfies FR-011).
4. Plots generated in `results/plots/`.

## Troubleshooting

- **Memory Error**: System automatically triggers subsampling (n=100). Check `data/processed/subsample_log.csv` for dropped queries.
- **Download Failure**: Retries up to 3 times. If persistent, check network.
- **Timeout**: If runtime > 5 hours, subsampling is forced.
