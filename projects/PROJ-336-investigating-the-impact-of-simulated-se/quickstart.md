# Quickstart: Investigating the Impact of Simulated Sensory Deprivation on Resting‑State Brain Network Dynamics

## Prerequisites

- **Python** 3.11+ (ensure the `python` command points to this version)
- **Git** (to clone the repository)
- **Internet connection** (required for downloading the OpenNeuro dataset and atlas files)
- **Environment variables**
 - `OPENNEURO_API_KEY` *(optional)* – API token if the OpenNeuro dataset requires authentication.
 - `DATA_ROOT` *(optional)* – Root directory for all pipeline data. If not set, defaults to the project‑relative `data/` folder.

## Installation

1. **Clone the repository**
 ```bash
 git clone https://github.com/your-org/your-repo.git
 cd your-repo
 ```

2. **Create a virtual environment and activate it**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install the required dependencies**
 ```bash
 pip install -r requirements.txt
 ```

## Running the full pipeline with a single subject

The pipeline can be executed end‑to‑end with a single command.
The `--sample 1` flag tells the orchestrator to process only one subject (useful for quick sanity checks and CI verification).

```bash
python -m src.main --sample 1
```

This command will:

1. **Download** one subject’s pre‑ and post‑deprivation resting‑state scans from OpenNeuro (or the fallback dataset).
2. **Run quality‑check** (framewise displacement) and exclude the subject if motion exceeds the default thresholds.
3. **Preprocess** the BOLD data (motion correction, MNI normalization, band‑pass filtering).
4. **Compute functional connectivity** matrices using the selected atlas.
5. **Calculate network metrics** (modularity, global efficiency, node strength).
6. **Perform statistical tests** (paired t‑test, FDR correction, permutation testing).
7. **Generate visualizations** (degree distributions, metric bar plots).

Upon successful completion the script exits with status 0 and the following output directories are populated:

- `data/preprocessed/` – preprocessed BOLD time series (`*.npy`)
- `data/connectivity/` – ROI‑wise correlation matrices (`*.npy`)
- `results/metrics.csv` – per‑subject metric table
- `results/stats.csv` – statistical test results
- `figures/` – PNG visualizations

## Dry‑run verification

CI validates the quickstart by executing a dry‑run:

```bash
python -m src.main --dry-run
```

The dry‑run prints the ordered pipeline stages without performing any heavy computation and must exit with status 0. [UNRESOLVED-CLAIM: c_37936879 — status=not_enough_info]

## Troubleshooting

- **Dataset download fails** – Verify internet connectivity and that the dataset ID (`ds001770` or fallback `ds003820`) is still available on OpenNeuro.
- **Missing deprivation labels** – The pipeline will abort with a clear error if the BIDS hierarchy does not contain the required `deprivation-{pre,post}` labels.
- **Memory or disk quota exceeded** – Reduce the `--sample` size or use the `--cleanup` flag after preprocessing to delete raw NIfTI files.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.