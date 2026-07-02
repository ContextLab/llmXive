# Docker Usage Guide

This document describes how to build and run the plant disease resistance prediction pipeline using Docker.

## Prerequisites

- Docker Engine installed on your system
- Docker Compose (optional, for multi-container setups)
- At least 8GB of RAM available for the build process

## Building the Docker Image

The Docker image is configured in the `Dockerfile` at the project root. It includes:
- Python 3.11 runtime
- `fastp` for quality control
- `bcftools` for variant calling and manipulation
- All project Python dependencies listed in `requirements.txt`

To build the image:

```bash
docker build -t plant-disease-pipeline:latest.
```

### Build Arguments (Optional)

You can customize the build using build arguments if needed (e.g., for specific versions):

```bash
docker build --build-arg PYTHON_VERSION=3.11 --build-arg FASTP_VERSION=0.23.2 -t plant-disease-pipeline:latest.
```

## Running the Pipeline

Once the image is built, you can run the pipeline. The container expects data to be mounted into the `data/` directory and will output results to `artifacts/`.

### Basic Run Command

```bash
docker run --rm -it \
 -v $(pwd)/data:/app/data \
 -v $(pwd)/artifacts:/app/artifacts \
 -v $(pwd)/code:/app/code \
 -e PYTHONPATH=/app \
 plant-disease-pipeline:latest \
 python code/main.py
```

### Running with Specific Arguments

The pipeline accepts standard CLI arguments via `code/main.py`. Example:

```bash
docker run --rm -it \
 -v $(pwd)/data:/app/data \
 -v $(pwd)/artifacts:/app/artifacts \
 -v $(pwd)/code:/app/code \
 -e PYTHONPATH=/app \
 plant-disease-pipeline:latest \
 python code/main.py --mode full --seed 42
```

### Resource Constraints

For production runs, it is recommended to limit resource usage to match the project constraints (RAM < 7GB, runtime < 6h):

```bash
docker run --rm -it \
 --memory="7g" \
 --cpus="4" \
 -v $(pwd)/data:/app/data \
 -v $(pwd)/artifacts:/app/artifacts \
 -v $(pwd)/code:/app/code \
 -e PYTHONPATH=/app \
 plant-disease-pipeline:latest \
 python code/main.py
```

## Simulated Mode vs Real Data

- **Simulated Mode**: If no real data is available, the pipeline can generate synthetic data. Ensure `data/data_manifest.yaml` has `source_type: SIMULATED` to bypass data integrity halts.
- **Real Data Mode**: When using real data, ensure all modalities (SNP, metabolite) are present and aligned. The pipeline will halt with `EX_DATA_INTEGRITY` or `EX_POWER_INSUFFICIENT` if requirements are not met.

## Troubleshooting

- **Permission Errors**: If you encounter permission errors when writing to `data/` or `artifacts/`, ensure the host directories are writable or run with `--user $(id -u):$(id -g)`.
- **Missing Tools**: If `fastp` or `bcftools` are missing, verify the `Dockerfile` build steps completed successfully.
- **Memory Issues**: If the container crashes due to OOM, increase the `--memory` limit or optimize the input dataset size.

## Cleaning Up

To remove the image after use:

```bash
docker image rm plant-disease-pipeline:latest
```
