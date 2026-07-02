# Predicting Plant Disease Resistance from Multi-omics Data

A reproducible machine learning pipeline for predicting plant disease resistance using SNP and metabolite data.

## Project Overview

This project implements an end-to-end pipeline that:
1. Downloads or generates multi-omics data (SNPs and metabolites)
2. Preprocesses and aligns data across modalities
3. Performs feature selection using LASSO and Random Forest
4. Trains predictive models (Elastic-Net, Gradient Boosting)
5. Validates models with permutation testing on hold-out sets
6. Generates biomarker reports and success criteria checks

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized execution)
- `fastp` and `bcftools` (if running on real sequencing data)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PROJ-259-predicting-plant-disease-resistance-from
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up directory structure:
```bash
python code/setup_directories.py
```

### Running the Pipeline

**Simulation Mode (Recommended for first run):**
```bash
python code/main.py --mode simulated
```

**Real Data Mode:**
Ensure `data/data_manifest.yaml` is configured with real accession numbers, then:
```bash
python code/main.py
```

## Docker Usage

For a consistent environment, we recommend using Docker.

### Build the Image

```bash
docker build -t plant-disease-pipeline:latest.
```

This image includes Python 3.11, `fastp`, `bcftools`, and all project dependencies.

### Run the Pipeline

```bash
docker run --rm -it \
 -v $(pwd)/data:/app/data \
 -v $(pwd)/artifacts:/app/artifacts \
 -v $(pwd)/code:/app/code \
 -e PYTHONPATH=/app \
 plant-disease-pipeline:latest \
 python code/main.py
```

**Resource Limits:**
To enforce the project's performance constraints (RAM < 7GB):
```bash
docker run --rm -it --memory="7g" --cpus="4" \
 -v $(pwd)/data:/app/data \
 -v $(pwd)/artifacts:/app/artifacts \
 -v $(pwd)/code:/app/code \
 -e PYTHONPATH=/app \
 plant-disease-pipeline:latest \
 python code/main.py
```

See `docs/Docker_usage.md` for detailed Docker instructions, troubleshooting, and advanced configurations.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Feature selection, modeling, validation
│ ├── data/ # Data download, generation, preprocessing
│ ├── utils/ # Logging, exceptions, stats
│ ├── config.py # Configuration management
│ └── main.py # CLI entry point
├── data/ # Data directory
│ ├── raw/ # Raw downloaded/generated data
│ └── processed/ # Preprocessed data
├── artifacts/ # Outputs
│ ├── models/ # Trained models
│ ├── reports/ # Metrics, biomarker reports
│ └── figures/ # Visualizations
├── docs/ # Documentation
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── Dockerfile # Container definition
```

## Key Features

- **Multi-omics Integration**: Aligns SNP and metabolite data by sample ID.
- **Robust Feature Selection**: Sensitivity sweep over thresholds with frequency aggregation.
- **Null Model Baselines**: Compares performance against random label baselines.
- **Permutation Testing**: Validates model significance on hold-out sets.
- **Success Criteria Checks**: Verifies minimum biomarker counts and performance targets.

## Configuration

Environment variables and default paths are managed in `code/config.py`.
Data sources are defined in `data/data_manifest.yaml`.

## License

[Insert License Information]

## Contributing

Please refer to the `CONTRIBUTING.md` (if available) for guidelines on adding new features or fixing bugs.
