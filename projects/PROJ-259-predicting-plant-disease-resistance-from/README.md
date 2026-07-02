# Predict Plant Disease Resistance from Multi-omics Data

This project implements a reproducible pipeline for predicting plant disease resistance using multi-omics data (SNPs and metabolites).

## Project Structure

- `code/`: Source code for the pipeline
- `data/`: Raw and processed data
- `artifacts/`: Trained models, reports, and figures
- `tests/`: Unit and integration tests
- `specs/`: Feature specifications and design documents

## Prerequisites

- Docker (for containerized execution)
- Python 3.11+ (for local development)
- Required Python packages listed in `requirements.txt`

## Quick Start with Docker

### Building the Docker Image

Build the Docker image using the provided `Dockerfile`:

```bash
docker build -t plant-disease-resistance:latest.
```

This image includes:
- Python 3.11 with project dependencies
- `fastp` for sequence preprocessing
- `bcftools` for variant calling and manipulation
- All project-specific Python packages

### Running the Pipeline

Execute the full pipeline inside the Docker container:

```bash
docker run --rm -v $(pwd):/workspace -w /workspace plant-disease-resistance:latest \
 python code/main.py
```

**Volume Mounting**: The `-v $(pwd):/workspace` flag mounts your current directory to `/workspace` inside the container, allowing the pipeline to:
- Read input data from `data/`
- Write processed data, models, and reports to `data/`, `artifacts/`, and `figures/`

**Working Directory**: The `-w /workspace` flag sets the working directory to the mounted volume.

### Running with Synthetic Data (Simulation Mode)

If no real data is available, the pipeline can generate synthetic data for testing:

```bash
docker run --rm -v $(pwd):/workspace -w /workspace plant-disease-resistance:latest \
 python code/main.py --simulate
```

This will:
- Generate ~150 paired samples with injected signal structure [UNRESOLVED-CLAIM: c_7bcf3025 — status=not_enough_info]
- Run the full pipeline on synthetic data
- Output results to `artifacts/reports/`

**Note**: In Simulation Mode, data integrity and power checks are bypassed per project specifications.

### Interactive Shell Access

For debugging or manual exploration:

```bash
docker run --rm -it -v $(pwd):/workspace -w /workspace plant-disease-resistance:latest bash
```

## Local Development (Without Docker)

### Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install System Dependencies

Ensure the following system tools are installed:
- `fastp`: `conda install -c bioconda fastp` or download from [fastp GitHub](https://github.com/OpenGene/fastp)
- `bcftools`: `conda install -c bioconda bcftools` or download from [samtools/bcftools](https://github.com/samtools/bcftools)

### Run the Pipeline

```bash
python code/main.py
```

## Output Artifacts

After a successful run, the following artifacts will be generated:

- `artifacts/reports/metrics.json`: Model performance metrics
- `artifacts/reports/selection_frequency.csv`: Feature selection frequency across thresholds
- `artifacts/reports/top_features.csv`: Ranked list of significant biomarkers
- `artifacts/reports/holdout_metrics.json`: Independent validation results
- `artifacts/models/`: Trained model files

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## Configuration

Environment variables can be set to customize paths and behavior:

- `DATA_DIR`: Path to raw data directory (default: `data/raw`)
- `OUTPUT_DIR`: Path to output directory (default: `artifacts`)
- `SIMULATE`: Set to `true` to enable simulation mode

## License

This project is licensed under the terms specified in the LICENSE file.