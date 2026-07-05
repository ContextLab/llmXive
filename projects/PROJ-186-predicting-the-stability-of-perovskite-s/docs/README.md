# Perovskite Stability Prediction Pipeline

## Overview

This project implements a machine learning pipeline to predict the thermodynamic stability (decomposition energy) of ABX₃ perovskite structures. The pipeline ingests data from the Materials Project, calculates physical descriptors (tolerance factor, octahedral factor, etc.), trains a Random Forest model, and performs virtual screening on hypothetical compounds.

## Prerequisites

- Python 3.11+
- pip
- API Key for Materials Project (set via `MP_API_KEY` environment variable)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd llmXive-proj-186
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

4. **Configure Environment Variables**:
 Create a `.env` file in the project root or set the environment variable directly:
 ```bash
 export MP_API_KEY="your_materials_project_api_key_here"
 ```

## Project Structure

```
.
├── code/ # Source code modules
│ ├── data/ # Data ingestion and processing
│ │ ├── download.py # Fetch data from Materials Project
│ │ ├── descriptors.py # Calculate physical descriptors
│ │ └── preprocess.py # Data cleaning and splitting
│ ├── models/ # Model training and prediction
│ │ ├── train.py # Train and evaluate models
│ │ └── predict.py # Virtual screening
│ ├── viz/ # Visualization scripts
│ │ └── plot.py # Generate plots
│ └── utils/ # Utility functions
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed features
├── results/ # Model artifacts and reports
├── specs/ # Project specifications
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── docs/ # Documentation
```

## Execution Instructions

The pipeline is designed to be run sequentially. Ensure all prerequisites from the previous step are met before starting.

### Step 1: Data Ingestion and Descriptor Calculation

This step fetches raw perovskite data from the Materials Project API, filters for cubic/rhombohedral structures, calculates physical descriptors, and saves the processed dataset.

```bash
# Run the full data pipeline
python code/data/download.py
python code/data/descriptors.py
python code/data/preprocess.py
python code/data/verify_nulls.py
```

**Outputs**:
- `data/processed/features.csv`: The final dataset with calculated descriptors.

### Step 2: Model Training

This step trains a Random Forest Regressor using 5-fold cross-validation, selects the best hyperparameters, and evaluates performance on a held-out test set.

```bash
python code/models/train.py
```

**Outputs**:
- `results/model.pkl`: The trained model artifact.
- `results/metrics.json`: Test set metrics (RMSE, R²).
- `results/model_metadata.json`: Model metadata including DFT functional used.

### Step 3: Visualization

Generate plots to visualize model performance and feature importance.

```bash
python code/viz/plot.py
```

**Outputs**:
- `results/predicted-vs-true.png`: Scatter plot of predicted vs. true values.
- `results/feature-importance.png`: Bar chart of feature importances.

### Step 4: Virtual Screening

Generate a combinatorial library of hypothetical perovskites, filter for geometric feasibility, predict stability, and rank candidates.

```bash
python code/models/predict.py
```

**Outputs**:
- `results/screening_full.csv`: Full list of ranked candidates.
- `results/screening_candidates.md`: Markdown report of top candidates.

## Validation and Quality Checks

The project includes several validation scripts to ensure data integrity and reproducibility.

### Verify Artifacts and Metrics
```bash
python code/quickstart_validate.py
```

### Verify Content Hashes
```bash
python code/run_hash_verification.py
```

### Verify Model Metadata
```bash
python code/run_verify_metadata.py
```

## Performance Constraints

The pipeline is optimized to run within the following constraints:
- **Time**: < 6 hours for full execution
- **Memory**: < 7 GB RAM
- **CPU**: Limited core usage (no GPU required)

These constraints are automatically checked during the validation phase.

## Troubleshooting

- **API Rate Limits**: The pipeline includes exponential backoff logic in `utils/api_client.py` to handle 429 errors from the Materials Project API.
- **Missing Data**: If the initial fetch yields fewer than 5,000 entries, the pipeline will attempt to merge with OQMD data (if configured) or raise an error.
- **Memory Errors**: If you encounter memory issues, ensure no other heavy processes are running and check the memory usage logs in `logs/pipeline.log`.

## License

This project is part of the llmXive automated science pipeline.