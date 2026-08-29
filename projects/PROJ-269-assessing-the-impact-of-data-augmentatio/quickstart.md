# Quickstart Guide: Assessing the Impact of Data Augmentation on Statistical Power

This guide provides instructions for running the full study pipeline to evaluate how data augmentation techniques (Gaussian Noise, SMOTE, Random Oversampling) affect Type I and Type II error rates in small-sample datasets.

## Prerequisites

- Python 3.8+
- pip
- Access to the internet (for initial dataset download)

## 1. Setup Environment

Navigate to the project root directory:

```bash
cd projects/PROJ-269-assessing-the-impact-of-data-augmentatio
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 2. Directory Structure

Ensure the following directory structure exists. The setup script (`code/main.py`) will create these if they are missing, but they can be manually created as follows:

```text
.
├── code/
├── tests/
├── data/
│ ├── raw/ # Downloaded UCI datasets
│ └── derived/ # Subsampled data and logs
├── results/ # Simulation output JSONs
├── contracts/ # JSON schemas
└── quickstart.md
```

## 3. Running the Full Pipeline

The entire study can be executed via the main orchestration script. This script handles:
1. Data download (UCI Breast Cancer, Ionosphere, Heart Disease)
2. Stratified subsampling (N=15, 25, 40)
3. Baseline simulation (Type I & II error estimation)
4. Augmentation simulation (Gaussian, SMOTE, RO)
5. Comparative analysis and threshold identification
6. Disclaimer injection and manifest updates

Run the pipeline:

```bash
python code/main.py
```

### Configuration

The pipeline is designed to run with default parameters defined in `code/simulation.py` and `code/main.py`.
- **Datasets**: Breast Cancer, Ionosphere, Heart Disease
- **Sample Sizes**: 15, 25, 40
- **Augmentation Methods**: Gaussian Noise, SMOTE, Random Oversampling
- **Threshold**: Type I error > 0.10 is flagged as "unsafe"

If you need to modify the simulation iterations or specific seeds, edit the `config` dictionary in `code/main.py` before running.

## 4. Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **Raw Data**: `data/raw/` (CSV files from UCI)
- **Derived Data**: `data/derived/` (Subsampled data, skipped configuration logs)
- **Results**: `results/`
 - `breast_cancer_15_baseline_null.json`
 - `breast_cancer_15_baseline_alt.json`
 - `breast_cancer_15_gaussian_null.json`
 -... (and so on for all combinations of dataset, size, and method)
- **Analysis**: `results/final_report.json` (Aggregated error rates, power, and threshold violations)
- **Manifest**: `data/derived/manifest.json` (SHA256 checksums of all result files)

## 5. Validation and Testing

To verify the implementation, run the test suite:

```bash
pytest tests/ -v
```

Key tests include:
- `tests/test_subsample.py`: Verifies stratified class ratio preservation.
- `tests/test_augment.py`: Checks zero-variance handling and noise injection.
- `tests/test_simulation.py`: Ensures deterministic reproducibility with pinned seeds.
- `tests/test_analysis.py`: Validates error rate calculations and threshold identification.

## 6. Troubleshooting

- **Data Fetch Errors**: If the dataset download fails, check your internet connection. The script will log warnings to `data/derived/fetch_count.log` if checksums do not match.
- **Memory Issues**: The pipeline is optimized for CPU-only execution with small sample sizes. If you encounter memory errors, ensure no other heavy processes are running.
- **CUDA Errors**: This project does not use GPU acceleration. If you see CUDA errors, ensure `imbalanced-learn` is installed in CPU mode (default).

## 7. Disclaimer

All result JSON files contain a `metadata.disclaimer` field stating:
> "DISCLAIMER: Findings are associational and do not imply causation. Statistical power estimates are specific to the sampled datasets and simulation parameters used."

This disclaimer is automatically injected by the `code/inject_disclaimer.py` module during the pipeline execution.