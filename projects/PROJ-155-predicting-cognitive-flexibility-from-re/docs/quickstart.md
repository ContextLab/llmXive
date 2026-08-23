# Quickstart Guide

## Project: Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability

This guide provides the minimum steps to set up and run the project pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- Access to HCP 1200 Subjects data (requires API token)

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

The project is organized as follows:
```
.
├── code/ # Source code modules
├── data/ # Data storage (raw, processed, results)
├── docs/ # Documentation
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── README.md # Project overview
```

## Configuration

Before running the pipeline, set up your environment:

1. Set your HCP API token:
 ```bash
 export HCP_API_TOKEN="your_token_here"
 ```

2. Verify configuration:
 ```bash
 python code/config.py --verify
 ```

## Running the Pipeline

Execute the full pipeline:
```bash
python code/main.py
```

Or run individual stages:
```bash
# Data download
python code/data/download.py

# Preprocessing
python code/data/preprocess.py

# Feature extraction
python code/features/connectivity.py

# Analysis
python code/analysis/regression.py
```

## Verification

Verify the project structure:
```bash
python code/setup_structure.py
```

Run tests:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Missing dependencies**: Ensure all packages in `requirements.txt` are installed.
- **API errors**: Verify your `HCP_API_TOKEN` is set correctly.
- **Memory issues**: Use batch processing with `--batch` flag for large datasets.

## Next Steps

- Read `docs/research.md` for detailed methodology
- Review `docs/technical-design.md` for implementation details
- Check `tests/` for unit and integration tests
