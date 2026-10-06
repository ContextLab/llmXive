# Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Project ID**: PROJ-537

This project implements an automated scientific pipeline to predict the yield strength of Body-Centered Cubic (BCC) steels. It integrates experimental yield strength data (from MatNavi/NIST) with Density Functional Theory (DFT) elastic constants (from the Materials Project API) to train and interpret machine learning models.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Output Artifacts](#output-artifacts)
- [Testing](#testing)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-537-predicting-the-yield-strength-of-bcc-ste
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Set up environment variables**:
 Create a `.env` file in the project root or set the following environment variable:
 ```bash
 export MP_API_KEY="your_materials_project_api_key"
 ```
 *Note: You can obtain an API key from [Materials Project](https://materialsproject.org/dashboard).*

5. **Set up Git hooks** (Optional but recommended):
 ```bash
 python code/setup_git_hooks.py
 ```

## Usage

The pipeline is orchestrated via `code/main.py`. You can run specific stages or the full pipeline.

### Run the Full Pipeline
Executes data ingestion, modeling, and interpretability analysis sequentially.
```bash
python code/main.py --full
```

### Run Individual Stages

**1. Ingestion (Data Integration)**
Fetches experimental and DFT data, merges them, and validates the dataset.
```bash
python code/main.py --stage ingestion
```
*Output*: `data/intermediate/merged.csv`, `data/provenance/dft_queries.jsonl`

**2. Modeling (Training & Evaluation)**
Trains Random Forest models (composition-only vs. DFT-enhanced) and performs statistical analysis.
```bash
python code/main.py --stage modeling
```
*Output*: `data/results/output.json`, `data/results/models/`

**3. Interpretability (SHAP & Stability)**
Generates TreeSHAP values, permutation importance, and bootstrap stability analysis.
```bash
python code/main.py --stage interpretability
```
*Output*: `data/results/shap_plots/`, `data/results/stability_analysis.json`

### Direct Script Execution
You can also run specific scripts directly from the `code/` directory:
```bash
# Fetch experimental data
python code/ingestion/fetch_experimental.py

# Fetch DFT data
python code/ingestion/fetch_dft.py

# Train models
python code/modeling/train.py
```

## Data Sources

This project relies on the following real, external data sources:

1. **Experimental Yield Strength Data**:
 - **Source**: MatNavi / NIST (via configured URL in `code/config.py`).
 - **Format**: CSV containing composition and yield strength values.
 - **Access**: Downloaded automatically by `code/ingestion/fetch_experimental.py`.

2. **DFT Elastic Constants**:
 - **Source**: Materials Project API.
 - **Data**: Elastic tensors, shear modulus, bulk modulus.
 - **Access**: Queried via `mp-api` or direct REST calls by `code/ingestion/fetch_dft.py`.
 - **Requirement**: Valid `MP_API_KEY` environment variable.

3. **Composition Data**:
 - Derived from the experimental dataset, processed into atomic fractions and one-hot encodings in `code/modeling/features.py`.

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration, paths, API keys
│ ├── main.py # Pipeline orchestration
│ ├── utils/ # Logging, checksums, seed verification
│ ├── ingestion/ # Data fetching, merging, validation
│ ├── modeling/ # Feature engineering, training, evaluation
│ └── interpretability/ # SHAP analysis, bootstrap stability
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── intermediate/ # Merged and cleaned datasets
│ ├── processed/ # Feature-engineered data
│ ├── provenance/ # Logs, checksums, query history
│ └── results/ # Model outputs, metrics, plots
├── tests/
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema contract tests
├── specs/ # Feature specifications
├── contracts/ # Data schemas
├── README.md
└── requirements.txt
```

## Configuration

Configuration is managed in `code/config.py`. Key settings include:

- `CONFIG.EXPERIMENTAL_DATA_URL`: URL for the experimental dataset.
- `CONFIG.MP_API_KEY`: Materials Project API key (loaded from env).
- `CONFIG.SEED`: Random seed for reproducibility (default: 42).
- `CONFIG.OUTPUT_PATHS`: Directories for intermediate and final results.

To modify paths or behavior, update `code/config.py` or set environment variables before running.

## Output Artifacts

Upon successful completion of the pipeline, the following artifacts are generated:

- **`data/intermediate/merged.csv`**: The unified dataset with experimental and DFT features (minimum 20 rows).
- **`data/provenance/dft_queries.jsonl`**: Log of all DFT API queries.
- **`data/provenance/checksums.txt`**: SHA-256 checksums for data integrity.
- **`data/results/output.json`**: Final metrics including R², MAE, p-values, statistical power, and stability checks.
- **`data/results/`**: Plots (SHAP summary, stability distributions).

## Testing

Run the test suite using `pytest`:

```bash
pytest tests/ -v
```

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/`
- **Contract Tests**: `tests/contract/`

Ensure the `MP_API_KEY` is set when running integration tests that query external APIs.