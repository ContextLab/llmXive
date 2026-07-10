# The Impact of Incidental Music on Autobiographical Memory Retrieval

## Project Overview

This project investigates the relationship between adolescent music exposure and the vividness/valence of autobiographical memories triggered by those songs. It implements a complete data science pipeline from raw data ingestion to statistical modeling and hypothesis testing.

## Key Research Questions

1. Does adolescent music exposure predict the vividness of autobiographical memories?
2. How does the emotional valence of memories relate to early musical experiences?
3. Are these relationships robust across different matching thresholds and permutation tests?

## Project Structure

```
.
├── code/ # Python implementation
│ ├── __init__.py
│ ├── config.py # Project configuration and paths
│ ├── data_ingestion.py # Data download and preprocessing
│ ├── cue_matching.py # Fuzzy string matching for music cues
│ ├── aggregation.py # Data aggregation to User-Track pairs
│ ├── modeling.py # Statistical modeling and hypothesis testing
│ ├── generate_diagnostic_plots.py
│ ├── generate_final_results.py
│ ├── generate_regression_summary.py
│ ├── generate_user_track_pairs.py
│ ├── setup_data_dirs.py
│ ├── state_manager.py
│ └── utils.py
├── data/
│ ├── raw/ # Raw downloaded datasets (MSD, AMT)
│ ├── processed/ # Intermediate processed data
│ └── final/ # Final analysis outputs
├── tests/ # Test suite
│ ├── unit/
│ └── integration/
├── specs/ # Project specifications
├── contracts/ # Data and output schemas
├── requirements.txt # Python dependencies
├── state.yaml # File checksum tracking
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-200-the-impact-of-incidental-music-on-autobi
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

4. Set up data directories:
 ```bash
 python code/setup_data_dirs.py
 ```

## Usage

### Running the Full Pipeline

The main orchestration script executes the complete analysis pipeline:

```bash
python code/main.py
```

This will:
1. Download raw datasets (MSD and AMT)
2. Filter and process cohort data
3. Calculate exposure scores
4. Match music cues to tracks
5. Aggregate data to User-Track pairs
6. Fit statistical models
7. Run sensitivity and permutation tests
8. Generate diagnostic plots and final results

### Running Individual Components

Each component can be run independently for testing or partial execution:

```bash
# Data ingestion
python code/data_ingestion.py

# Cue matching
python code/cue_matching.py

# Aggregation
python code/aggregation.py

# Modeling
python code/modeling.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/test_ingestion.py
pytest tests/unit/test_matching.py
pytest tests/unit/test_modeling.py
```

## Data Sources

- **Million Song Dataset (MSD)**: Music track metadata and listening logs
- **Autobiographical Memory Test (AMT)**: Free-text memory cues and associated metadata

Both datasets are downloaded from their canonical sources during the data ingestion phase.

## Output Files

The pipeline generates the following outputs in `data/final/`:

- `regression_summary.csv`: Model coefficients, standard errors, and p-values
- `sensitivity_analysis.csv`: Results across different Levenshtein thresholds
- `permutation_results.csv`: Permutation test statistics and p-values
- `plots/`: Diagnostic plots (residuals, QQ plots, etc.)

## Configuration

Project configuration is managed in `code/config.py`. Key parameters include:

- Levenshtein distance threshold for cue matching (default: 4)
- Minimum listen threshold for track filtering (default: 10)
- Random seeds for reproducibility
- File paths for data directories

## Statistical Methods

### Primary Analysis

Linear mixed-effects models are fitted with the formula:
```
mean_vividness ~ residualized_exposure + popularity + (1|user_id)
```

Where:
- `residualized_exposure`: Adolescent exposure score adjusted for overall track popularity
- `popularity`: Overall track popularity score
- `user_id`: Random effect to account for individual differences

### Sensitivity Analysis

The analysis is repeated across different Levenshtein distance thresholds (2, 4, 6) to assess robustness.

### Permutation Test

A block-permutation test is performed on User-Track pairs to establish statistical significance, shuffling exposure scores while preserving the User-Track grouping structure.

## Dependencies

See `requirements.txt` for the complete list of dependencies:

- pandas
- numpy
- scikit-learn
- statsmodels
- python-Levenshtein
- pyyaml
- tqdm
- scipy
- matplotlib
- seaborn

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure nothing is broken
5. Submit a pull request

## Contact

For questions or issues, please open an issue in the repository.
