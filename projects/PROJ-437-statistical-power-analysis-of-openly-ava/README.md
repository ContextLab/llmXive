# Statistical Power Analysis of Openly Available fMRI Datasets

This project implements an automated pipeline to estimate statistical power for replication of fMRI studies using openly available datasets (OpenNeuro). It performs end-to-end analysis including data download, preprocessing (ROI extraction, temporal smoothing), GLM fitting, split-half validation, and power curve generation.

## Requirements

- Python 3.11+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Power curve, GLM, validation logic
│ ├── download/ # Data fetching and validation
│ ├── models/ # Data models (SimulationConfig, ReplicationResult)
│ ├── preprocess/ # ROI extraction, temporal smoothing
│ ├── simulation/ # Noise estimation
│ ├── utils/ # Seed manager, memory monitor
│ └── main.py # Pipeline entry point
├── data/ # Data storage
│ ├── raw/ # Downloaded BIDS datasets
│ ├── derived/ # Preprocessed data (ROI timeseries)
│ └── aggregated/ # Power curve results
├── results/ # Output reports
│ └── paper/ # Final reports (sensitivity, timing, etc.)
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── README.md # This file
```

## CLI Usage

The main entry point is `code/main.py`. It orchestrates the full pipeline for a single dataset or a multi-paradigm analysis.

### Basic Pipeline Run

Run the pipeline on a specific dataset (e.g., `ds000030`) with a fixed sample size:

```bash
python code/main.py \
 --dataset ds000030 \
 --sample-size 10 \
 --smoothing-kernel 4 \
 --seed 42 \
 --output results/pipeline_run_001.json
```

### Multi-Paradigm Power Curve Generation

Generate power curves across multiple cognitive paradigms and sample sizes:

```bash
python code/main.py \
 --mode power-curve \
 --paradigms motor working_memory emotion_processing \
 --sample-sizes 10 20 30 40 \
 --kernels 4 8 \
 --iterations 100 \
 --output data/aggregated/power_curves.json
```

### Sensitivity Analysis

Run sensitivity analysis across different smoothing kernels and alpha levels:

```bash
python code/main.py \
 --mode sensitivity \
 --paradigms motor working_memory \
 --kernels 4 8 \
 --alphas 0.01 0.05 0.1 \
 --output results/paper/sensitivity_report.md
```

### Configuration File (Optional)

You can provide a YAML configuration file to specify default parameters:

```bash
python code/main.py --config config.yaml
```

Example `config.yaml`:

```yaml
dataset: ds000030
sample_size: 10
smoothing_kernel: 4
random_seed: 42
iterations: 50
output_dir: results/
```

## Output Files

- `results/pipeline_run_001.json`: Single run replication result (binary success/failure).
- `data/aggregated/power_curves.json`: Empirical power rates for tested sample sizes.
- `data/aggregated/corrected_power_curves.json`: FDR-corrected power estimates.
- `results/paper/sensitivity_report.md`: Comparison of preprocessing parameters.
- `results/paper/alpha_sensitivity_report.md`: Sensitivity to alpha level changes.
- `results/paper/timing_report.md`: Wall-clock execution time metrics.
- `results/paper/pipeline_config.json`: Traceability log of pipeline parameters.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test categories:

```bash
pytest tests/contract/ -v # Contract tests
pytest tests/unit/ -v # Unit tests
pytest tests/integration/ -v # Integration tests
```

## Reproducibility

- All random seeds are controlled via `--seed` or `random_seed` in config.
- Memory usage is monitored; the pipeline will downsample or fail if thresholds are exceeded.
- Real data only: The pipeline will fail loudly if data cannot be fetched from OpenNeuro.

## License

This project is licensed under the MIT License.

## Contact

For questions or issues, please open an issue in the repository.