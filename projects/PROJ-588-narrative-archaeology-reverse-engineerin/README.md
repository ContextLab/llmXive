# Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

This project implements the analysis pipeline for reverse-engineering story memories from fMRI brain data, focusing on the distinction between early and late event patterns in the hippocampus and mPFC.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd narrative-archaeology
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

4. For development (optional):
 ```bash
 pip install -e ".[dev]"
 ```

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── data/ # Data ingestion and preprocessing
│ ├── models/ # Analysis models (RSA, decoding)
│ └── utils/ # Utilities (stats, visualization)
├── data/ # Data storage (downloaded datasets, preprocessed files)
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
└── README.md # This file
```

## Configuration

Before running any analysis, ensure `code/config.py` is properly configured with:
- Random seeds for reproducibility
- CPU-only constraints (no GPU usage)
- Correct paths to data directories
- Motion artifact thresholds

## Running the Pipeline

The pipeline consists of several stages:

1. **Data Download**: Download OpenNeuro datasets (e.g., ds000234)
2. **Preprocessing**: Run fMRIPrep or nilearn-based preprocessing
3. **Segmentation**: Align story events to BOLD signal
4. **ROI Extraction**: Extract timecourses from hippocampus, mPFC, PCC, etc.
5. **Analysis**:
 - RSA: Compare early vs. late event patterns
 - Decoding: Predict narrative elements from neural patterns

Example usage:
```bash
# Run preprocessing
python code/data/preprocess.py --subject sub-01

# Run RSA analysis
python code/models/rsa.py --roi mPFC

# Run decoding analysis
python code/models/decoder.py --category plot
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## License

MIT License
