# Reconstructing Solar Irradiance from Historical Sunspot Records

Automated pipeline for reconstructing Total Solar Irradiance (TSI) using historical sunspot records.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Configure environment variables**:
 - Copy the example environment file:
 ```bash
 cp code/.env.example code/.env
 ```
 - Edit `code/.env` to set your specific configuration (e.g., data paths, API keys if needed).

## Usage

### Running the Pipeline

The pipeline is executed through a series of scripts in the `code/` directory.

1. **Setup Environment**:
 ```bash
 python code/env_manager.py
 ```

2. **Data Ingestion**:
 ```bash
 python code/data/ingestion.py
 ```

3. **Preprocessing**:
 ```bash
 python code/data/preprocessing.py
 ```

4. **Model Training**:
 ```bash
 python code/models/train.py
 ```

5. **Prediction/Reconstruction**:
 ```bash
 python code/models/predict.py
 ```

6. **Analysis & Reporting**:
 ```bash
 python code/analysis/comparison.py
 ```

### Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
.
├── code/
│ ├──.env # Local environment configuration (not committed)
│ ├──.env.example # Template for environment configuration
│ ├── env_manager.py # Environment variable management
│ ├── config.py # Project configuration constants
│ ├── data/
│ │ ├── ingestion.py # Data fetching from external sources
│ │ └── preprocessing.py # Data cleaning and transformation
│ ├── models/
│ │ ├── train.py # Model training pipeline
│ │ ├── predict.py # Model inference and reconstruction
│ │ └── train_fallback.py# Fallback model training
│ └── analysis/
│ ├── comparison.py # Baseline and CMIP6 comparison
│ ├── stats.py # Statistical analysis
│ └── sensitivity.py # Sensitivity analysis
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data artifacts
├── tests/ # Test suite
└── requirements.txt # Python dependencies
```

## Environment Variables

The project uses environment variables for configuration. See `code/.env.example` for available options:

- `DATA_ROOT_DIR`: Root directory for data artifacts.
- `DATA_RAW_DIR`: Subdirectory for raw data.
- `DATA_PROCESSED_DIR`: Subdirectory for processed data.
- `SILSO_BASE_URL`: Base URL for SILSO sunspot data.
- `SORCE_BASE_URL`: Base URL for SORCE TSI data.
- `MODEL_ARTIFACTS_DIR`: Directory for saved models.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Run tests: `pytest tests/ -v`
5. Submit a pull request.

## License

[License Information]