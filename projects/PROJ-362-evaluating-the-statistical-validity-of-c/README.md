# Evaluating the Statistical Validity of Common Ranking Metrics

This project implements a rigorous statistical validation pipeline for ranking metrics (NDCG@10, MAP) using permutation tests on TREC Robust04 and TREC Web data. It calculates p-values, applies Benjamini-Hochberg correction, estimates Minimum Detectable Effect Size (MDES), and generates visualizations.

## Installation

1. **Prerequisites**: Python 3.10 or higher.

2. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-362-evaluating-the-statistical-validity-of-c
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Verify environment**:
 Ensure you have write permissions for the `data/` and `results/` directories.

## Usage

The pipeline is driven by `code/main.py`. All data is fetched from TREC sources via HuggingFace `datasets` (see `data_loader.py`).

### Configuration

Key parameters (seeds, permutation counts, paths) are defined in `code/config.py`.

### Running Modes

The script supports independent modes that can be chained or run separately:

- **Data Loading**: Fetches TREC Robust04 and Web data, validates schemas.
 ```bash
 python code/main.py --mode data_load
 ```

- **Permutation Tests**: Executes permutation tests to generate null distributions and raw p-values.
 ```bash
 python code/main.py --mode permutation
 ```

- **P-Value Correction**: Applies Benjamini-Hochberg correction to raw p-values.
 ```bash
 python code/main.py --mode p_values
 ```

- **Power Analysis**: Calculates MDES and performs sensitivity analysis.
 ```bash
 python code/main.py --mode power_analysis
 ```

- **Reporting**: Generates summary CSVs and density plots.
 ```bash
 python code/main.py --mode report
 ```

- **All Modes**: Runs the full pipeline sequentially (Data Load → Permutation → P-Values → Power Analysis → Report).
 ```bash
 python code/main.py --mode all
 ```

### Resource Constraints

The pipeline includes runtime and memory guards (see `code/main.py`). If runtime exceeds 5 hours or memory usage exceeds 6GB, the system will trigger subsampling or exit with a warning to prevent resource exhaustion.

## Output Artifacts

All outputs are generated under the `results/` directory (paths defined in `code/config.py`).

| Directory | File | Description |
|:--- |:--- |:--- |
| `results/null_distributions/` | `query_<id>_ndcg.csv` | Null distribution scores for NDCG@10 per query. |
| `results/null_distributions/` | `query_<id>_map.csv` | Null distribution scores for MAP per query. |
| `results/p_values/` | `raw_p_values.csv` | Raw p-values for all query-metric pairs. |
| `results/p_values/` | `corrected_p_values.csv` | BH-corrected p-values and significance flags. |
| `results/mdes/` | `mdes_summary.csv` | Minimum Detectable Effect Size estimates with confidence intervals. |
| `results/sensitivity/` | `alpha_sweep.csv` | Sensitivity analysis results across different alpha thresholds. |
| `results/plots/` | `density_<query_id>_<metric>.png` | Density plots comparing observed vs. permuted scores. |
| `results/` | `summary.csv` | Aggregated summary of all metrics, p-values, and MDES. |

## Project Structure

```text
.
├── code/
│ ├── config.py # Configuration constants
│ ├── data_loader.py # TREC data fetching & validation
│ ├── metrics.py # NDCG & MAP calculation
│ ├── permutation.py # Permutation test engine
│ ├── power_analysis.py # MDES & Power analysis
│ ├── visualization.py # Plot generation
│ ├── main.py # CLI entry point
│ └──... (helpers)
├── data/
│ └── raw/ # Downloaded TREC data (if cached)
├── results/ # Generated outputs
├── tests/ # Unit and integration tests
├── requirements.txt # Dependencies
└── README.md
```

## License

This project is for research purposes. Data usage complies with TREC data policies.