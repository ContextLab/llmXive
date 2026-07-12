# Quickstart Guide: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

This guide provides instructions for setting up, running, and analyzing the gravitational wave (GW) resolution impact pipeline.

## Prerequisites

- Python 3.9+
- pip and virtual environment tools
- Access to the GWOSC API (internet connection required)

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Configuration

Ensure the `code/config.py` file is configured with your desired data paths.
By default, data is stored in:
- `data/raw/`: Raw strain data from GWOSC
- `data/derived/`: Processed (downsampled/quantized) data
- `results/posteriors/`: Posterior samples from `bilby` runs
- `results/metrics/`: Calculated bias and divergence metrics

## Running the Pipeline

The pipeline is executed in three main phases corresponding to the User Stories.

### Phase 1: Data Download and Transformation (User Story 1)

Download high-SNR events and apply resolution transforms.

```bash
python code/data/download.py
python code/data/transform.py
```

*Note: This step requires fetching data from GWOSC. Ensure you have network access.*

### Phase 2: Bayesian Inference (User Story 1)

Run parameter estimation using `bilby` and `dynesty`.

```bash
python code/inference/run_bilby.py
```

This generates posterior files for each resolution configuration.
Convergence is checked via `dlogz < 0.1`. Runs exceeding the maximum steps with `dlogz > 0.1` are flagged as "inconclusive".

### Phase 3: Metrics Calculation (User Story 2)

Calculate Hellinger distance and bias metrics against the baseline (4096 Hz).

```bash
python code/analysis/metrics.py
```

This step gates on the validity of the baseline posterior.

### Phase 4: Aggregation and Visualization (User Story 3)

Aggregate results across events and generate summary reports.

```bash
python code/analysis/aggregate.py
python code/analysis/visualize.py
```

## Output Artifacts

- **Posterior Files**: `results/posteriors/{event_id}_{resolution}_posterior.hdf5`
- **Metrics JSON**: `results/metrics/{event_id}_metrics.json`
- **Aggregation Report**: `results/metrics/aggregation_report.json`
- **Visualizations**: `figures/bias_vs_sampling_rate.png`

## Troubleshooting

- **Convergence Failures**: If many runs are flagged "inconclusive", consider increasing the `dlogz` threshold or `maxiter` in `code/inference/run_bilby.py` (requires spec update).
- **Missing Data**: The pipeline logs warnings for missing GWOSC segments. Check `logs/derivation.log` for segment IDs.
- **Seed Reproducibility**: All random seeds are enforced via `code/utils/seeds.py`. Do not modify `numpy` or `bilby` seeds elsewhere in the code.

## Contributing

Please refer to the `CONTRIBUTING.md` file for development guidelines.
