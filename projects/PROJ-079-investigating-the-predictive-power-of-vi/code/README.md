# Predictive Modeling of Host Immune Response from Viral Sequence Features

This project implements a pipeline to investigate the predictive power of viral sequence features on host immune response. It integrates viral genomic data from NCBI and host transcriptomic data from GEO to train and evaluate predictive models.

## Project Structure

```
.
├── code/
│ ├── src/ # Source code
│ │ ├── config.py # Configuration constants
│ │ ├── download.py # Data acquisition from NCBI and GEO
│ │ ├── preprocess.py # Data normalization and ISG scoring
│ │ ├── features.py # Viral sequence feature extraction
│ │ ├── model.py # Model training and evaluation
│ │ ├── viz.py # Visualization of results
│ │ ├── main.py # Pipeline orchestration
│ │ └── models/ # Pydantic data models
│ ├── tests/ # Unit and integration tests
│ └── utils/ # Logging and timeout utilities
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed and merged datasets
│ ├── interim/ # Intermediate processing files
│ └── artifacts/ # Final model outputs and plots
├── specs/ # Project specifications and design docs
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # 5-minute run guide
```

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-079-investigating-the-predictive-power-of-vi
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

4. **Set up environment variables**:
 Copy `.env.example` to `.env` and fill in your API keys:
 ```bash
 cp.env.example.env
 # Edit.env to add NCBI_API_KEY and GEO_ACCESSIONS
 ```

## Data Requirements

The pipeline requires:
- **Viral Genomes**: Downloaded from NCBI Virus API. Accession list must be provided in `.env` or via command line.
- **Host Expression Data**: Downloaded from NCBI GEO. Series matrix files are expected.
- **ISG Gene Sets**: A predefined list of Interferon-Stimulated Genes (ISGs) for the target species.

Ensure sufficient disk space for raw and processed data (typically 1–5 GB depending on the number of samples).

## Usage

### Running the Full Pipeline

Execute the main pipeline script:
```bash
python -m src.main
```

This will:
1. Download viral genomes and GEO expression data.
2. Preprocess expression data and calculate ISG scores.
3. Extract viral sequence features (k-mers, GC content, stability, etc.).
4. Merge datasets and aggregate by strain.
5. Train an Elastic Net model and compute Debiased Lasso p-values.
6. Generate performance metrics and visualizations.

### Running Specific Steps

You can run individual components by importing and calling their functions directly:

```python
from src.download import fetch_viral_genomes, fetch_geo_data
from src.preprocess import normalize_counts, calculate_isg_score
from src.features import extract_sequence_features
from src.model import train_elastic_net, evaluate_model
```

### Configuration

Edit `src/config.py` to modify paths, timeouts, and API base URLs:
- `DATA_RAW_PATH`: Directory for raw downloads.
- `DATA_PROCESSED_PATH`: Directory for processed data.
- `ARTIFACTS_PATH`: Directory for model outputs and plots.
- `SEED`: Random seed for reproducibility.
- `MAX_RUNTIME_HOURS`: Maximum allowed runtime (4 hours by default).

## Output Artifacts

After successful execution, the following artifacts are generated:

- `data/processed/merged_dataset.csv`: Combined features and ISG scores.
- `data/processed/aggregated_dataset.csv`: Strain-aggregated data.
- `data/artifacts/models/elastic_net.pkl`: Trained model.
- `data/artifacts/metrics.json`: Performance metrics (R², RMSE, p-values).
- `data/artifacts/plots/coefficients.png`: Feature coefficient plot.
- `data/artifacts/plots/pdp_top5.png`: Partial dependence plots for top features.

## Testing

Run the test suite with pytest:
```bash
pytest tests/ -v --cov=src
```

Ensure coverage is above 80% for core modules.

## License

This project is for research purposes only.
