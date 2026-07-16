# PROJ-349: Predicting the Impact of Ball Milling on Particle Size Distribution

## Overview
This project implements an automated science pipeline to predict the impact of ball milling parameters on particle size distribution (PSD) using machine learning models.

## Prerequisites
- Python 3.11+
- pip (latest version)
- Poppler utilities (for PDF image extraction, required by pdf2image)
 - Ubuntu/Debian: `sudo apt-get install poppler-utils`
 - macOS: `brew install poppler`
 - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/ and add to PATH

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd proj-349-predicting-the-impact-of-ball-milling-on
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

4. Set up environment variables (optional, for API keys):
 ```bash
 cp.env.example.env
 # Edit.env and add your API keys (e.g., MATERIALS_PROJECT_API_KEY)
 ```

## Project Structure
```
.
├── code/
│ ├── src/
│ │ ├── ingest/ # Data ingestion modules
│ │ ├── preprocess/ # Data preprocessing pipelines
│ │ ├── model/ # Model training and evaluation
│ │ ├── interpret/ # Model interpretability tools
│ │ ├── cli/ # Command-line interfaces
│ │ ├── utils/ # Utility functions
│ │ ├── exceptions.py # Custom exceptions
│ │ └──...
│ ├── tests/ # Test suite
│ ├── setup_data_dirs.py # Data directory setup script
│ └──...
├── data/
│ ├── raw/ # Raw data from sources
│ ├── processed/ # Preprocessed data
│ ├── splits/ # Train/test splits (dynamic)
│ └──...
├── results/ # Model outputs and reports
├── contracts/ # Data schemas and contracts
├── requirements.txt # Pinned dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Quick Start

### 1. Setup Data Directories
```bash
python code/setup_data_dirs.py
```

### 2. Run Data Ingestion Pipeline
```bash
python code/src/cli/ingest.py
```
This will:
- Fetch data from Materials Project, NIST, and arXiv
- Merge and deduplicate records
- Preprocess data (imputation, encoding, scaling)
- Validate schema and output size
- Save processed data to `data/processed/`

### 3. Train Models
```bash
python code/src/cli/train.py
```
This will:
- Attempt GPR training with resource monitoring
- Fall back to Random Forest if resource limits exceeded (>30min or >5GB RAM)
- Run nested cross-validation
- Calculate evaluation metrics
- Perform statistical tests

### 4. Interpret Models
```bash
python code/src/cli/interpret.py
```
This will:
- Generate partial dependence plots
- Export feature importance rankings

## Running Tests
```bash
pytest code/tests/
```

## Linting and Formatting
```bash
# Check code style
flake8 code/src/
black --check code/src/
isort --check code/src/

# Format code
black code/src/
isort code/src/
```

## Contributing
Please read the contribution guidelines before submitting pull requests.

## License
[License information]

## Acknowledgments
- Materials Project API
- NIST Repository
- arXiv
- llmXive Research Team
