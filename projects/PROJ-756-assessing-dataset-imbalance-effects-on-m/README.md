# PROJ-756: Assessing Dataset Imbalance Effects on Materials Property Predictions

This project investigates how dataset imbalance (both in target properties and compositional feature space) impacts the performance of machine learning models trained to predict material properties.

## Project Structure

```text
PROJ-756-assessing-dataset-imbalance-effects-on-m/
├── code/ # Python implementation modules
│ ├── main.py # Entry point for the full pipeline
│ ├── ingestion.py # API ingestion with exponential backoff
│ ├── downloaders.py # Data downloaders (OQMD, AFLOW, MP)
│ ├── descriptors.py # Magpie descriptor computation
│ ├── imbalance.py # Imbalance score calculations
│ ├── training.py # Model training (RF, GB)
│ ├── evaluation.py # Model evaluation and statistics
│ ├── resampling.py # Resampling logic (binning, SMOTE fallback)
│ ├── shap_analysis.py # Synthetic ground truth generation
│ ├── shap_compute.py # SHAP value computation
│ ├── shap_ranking.py # Rank shift analysis
│ ├── shap_validation.py # SHAP validation against ground truth
│ ├── statistical_tests.py # Statistical significance testing
│ ├── correlation_analysis.py # Correlation between imbalance and performance
│ ├── verify_no_synthetic_fallback.py # Safety check
│ └── verify_streaming_strategy.py # Streaming verification
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets (parquet)
│ └── processed/ # Processed data (descriptors)
├── results/ # Analysis outputs
│ ├── target_imbalance_scores.csv
│ ├── compositional_imbalance_score.csv
│ ├── baseline_report.csv
│ ├── performance_degradation.csv
│ ├── comparison_report.csv
│ ├── correlation_analysis.csv
│ ├── statistical_test_results.csv
│ └── shap_analysis/ # SHAP artifacts
├── tests/ # Unit, contract, and integration tests
├── state/ # Pipeline state tracking
├── logs/ # Execution logs
├── artifacts/ # Additional artifacts
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites

- Python 3.11+
- pip
- API keys (optional):
 - Materials Project (MP_API_KEY environment variable)
 - OQMD (if required by specific endpoints)

## Setup

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
4. **Set environment variables** (optional):
 ```bash
 export MP_API_KEY="your_materials_project_api_key"
 ```

## Quick Start

### Run the Full Pipeline

To execute the entire pipeline (ingestion → descriptors → imbalance analysis → training → evaluation → resampling → SHAP analysis):

```bash
python code/main.py --full-pipeline --include-mp --streaming
```

- `--full-pipeline`: Runs all stages sequentially.
- `--include-mp`: Attempts to fetch Materials Project data (requires valid API key).
- `--streaming`: Uses streaming mode for large datasets to stay within memory constraints.

### Fallback Mode (No Materials Project)

If Materials Project is unavailable or you want to run with OQMD/AFLOW only:

```bash
python code/main.py --full-pipeline --fallback-mode --streaming
```

### Run Specific Stages

- **Ingestion & Download**:
 ```bash
 python code/ingestion.py
 ```
- **Descriptor Computation**:
 ```bash
 python code/descriptors.py
 ```
- **Imbalance Analysis**:
 ```bash
 python code/imbalance.py
 ```
- **Training & Evaluation**:
 ```bash
 python code/training.py
 python code/evaluation.py
 ```
- **Resampling**:
 ```bash
 python code/resampling.py
 ```
- **SHAP Analysis**:
 ```bash
 python code/shap_analysis.py
 python code/shap_compute.py
 python code/shap_ranking.py
 python code/shap_validation.py
 ```

### Run Tests

- **Unit Tests**:
 ```bash
 pytest tests/unit/
 ```
- **Contract Tests**:
 ```bash
 pytest tests/contract/
 ```
- **Integration Tests**:
 ```bash
 pytest tests/integration/
 ```

## Output Artifacts

After a successful run, the following key files will be generated:

- `results/target_imbalance_scores.csv`: Gini coefficients for target properties.
- `results/compositional_imbalance_score.csv`: Gini coefficients for compositional clusters.
- `results/baseline_report.csv`: Performance metrics (MAE, R2, RMSE) for skewed data.
- `results/performance_degradation.csv`: Performance difference on minority subsets.
- `results/comparison_report.csv`: Detailed comparison between skewed and balanced models.
- `results/correlation_analysis.csv`: Correlation between imbalance scores and performance degradation.
- `results/statistical_test_results.csv`: Results of paired t-tests/Wilcoxon tests.
- `results/shap_analysis/`: Contains SHAP values, rank shifts, and validation reports.

## Data Integrity & Safety

- **Fail Loudly**: Data loaders are configured to raise `DataFetchError` on persistent API failures. No synthetic fallback data is generated.
- **No Synthetic Fallback Verification**: Run `python code/verify_no_synthetic_fallback.py` to ensure no synthetic data generation code paths exist.
- **Streaming**: Large datasets are processed in chunks to avoid memory overflow.

## License

This project is part of the llmXive automated science pipeline.