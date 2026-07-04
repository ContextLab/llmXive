# Installation Guide

## System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Python**: Version 3.11 or higher
- **Memory**: Minimum 4GB RAM recommended
- **Disk Space**: At least 2GB free space for datasets and outputs

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PROJ-092-statistical-analysis-of-feature-importan
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Or using conda
conda create -n feature-drift python=3.11
conda activate feature-drift
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

### 4. Set Up Directory Structure

Run the directory setup script:

```bash
python code/setup_directories.py
```

This creates:
- `data/raw/`
- `data/processed/`
- `outputs/`
- `figures/`

### 5. Download the Dataset

```bash
python code/download.py
```

This downloads the UCI Electricity Load Diagrams dataset to `data/raw/`.

### 6. Run the Pipeline

```bash
python code/main.py
```

### 7. Verify Installation

Run the tests:

```bash
pytest tests/
```

## Configuration

### Environment Variables

The pipeline supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_DIR` | Base directory for data | `data` |
| `OUTPUT_DIR` | Directory for outputs | `outputs` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `WINDOW_SIZE_DAYS` | Size of time windows | `30` |
| `MIN_R_SQUARED` | Minimum R² for valid models | `0.8` |

Example:

```bash
export DATA_DIR=/path/to/data
export LOG_LEVEL=DEBUG
python code/main.py
```

### Configuration File

For advanced configuration, you can modify `code/utils/config.py` directly or create a custom configuration class.

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'utils'"

Ensure you are running scripts from the project root or adjust the Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
```

#### "Dataset download failed"

- Check your internet connection
- Verify the UCI archive URL is accessible
- Try downloading manually from: https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip

#### "Memory error during processing"

- Reduce the window size in `code/utils/config.py`
- Process data in smaller batches
- Increase available RAM

### Getting Help

- Check the [README.md](README.md) for usage examples
- Review the [tasks.md](../tasks.md) for implementation details
- Open an issue on the repository

## Next Steps

After successful installation:

1. Read the [README.md](README.md) for pipeline overview
2. Run the full pipeline with `python code/main.py`
3. Explore the outputs in the `outputs/` directory
4. Run drift analysis with `python code/drift_analysis.py`
5. Generate the final report with `python code/generate_final_report.py`
