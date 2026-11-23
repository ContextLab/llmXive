# Predicting Antibiotic Resistance Evolution from Genomic Sequences

A reproducible machine learning pipeline to predict antibiotic resistance in *E. coli* using genomic sequences, phylogenetic analysis, and mechanism-blind validation.

## Project Overview

This project implements a complete scientific pipeline to:
1. Ingest *E. coli* genomic sequences and metadata from NCBI
2. Process sequences to identify SNPs, resistance genes, and copy number variations
3. Train predictive models (Logistic Regression, Random Forest) with phylogenetically-aware validation
4. Perform statistical significance testing and sensitivity analysis
5. Generate visualizations and comprehensive reports

## Key Features

- **Phylogenetically-Blocked Cross-Validation**: Prevents data leakage by splitting based on evolutionary clades
- **Mechanism-Blind Filtering**: Excludes known resistance genes for the target antibiotic class to prevent circular reasoning
- **Reproducible Pipeline**: Full pipeline re-execution script with artifact verification
- **Statistical Rigor**: Phylogenetically-aware permutation testing for significance validation

## Project Structure

```
PROJ-027-predicting-antibiotic-resistance-evoluti/
├── code/
│ ├── 01_ingest/ # Data ingestion scripts
│ │ ├── download_ncbi.py # Fetch sequences from NCBI
│ │ ├── ingest_metadata.py # Parse susceptibility metadata
│ │ └── download_card.py # Fetch CARD resistance gene data
│ ├── 02_process/ # Sequence processing
│ │ ├── run_snippy.sh # SNP calling wrapper
│ │ ├── run_ariba.sh # Resistance gene detection
│ │ ├── build_feature_matrix.py # Aggregate features
│ │ └── generate_phylogeny.py # Phylogenetic tree inference
│ ├── 03_model/ # Model training and evaluation
│ │ ├── mechanism_blind_filter.py
│ │ ├── split_data.py
│ │ ├── train_models.py
│ │ ├── evaluate.py
│ │ └── save_models.py
│ ├── 04_validate/ # Statistical validation
│ │ └── sensitivity_analysis.py
│ ├── validate/ # Phylogenetic validation
│ │ └── phylo_permutation.py
│ ├── 05_viz/ # Visualization
│ │ └── generate_plots.py
│ ├── utils/ # Utility modules
│ │ ├── logging.py
│ │ ├── config.py
│ │ └── hash_artifacts.py
│ ├── setup_*.py # Project setup scripts
│ └── main_reproducible.py # Full pipeline re-execution
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed feature matrices
│ └── models/ # Trained model artifacts
├── tests/
│ ├── contract/ # Schema validation tests
│ └── unit/ # Unit tests
├── docs/ # Documentation
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.11+
- pip package manager
- System dependencies: `snippy`, `ariba`, `fasttree` (for phylogeny)
- Internet access for NCBI and CARD database downloads

## Installation

1. Clone the repository and navigate to the project directory:
```bash
git clone <repository-url>
cd PROJ-027-predicting-antibiotic-resistance-evoluti
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r code/requirements.txt
```

4. Verify environment setup:
```bash
python code/verify_env.py
```

5. Create required directory structure:
```bash
python code/setup_directories.py
```

## Quick Start

### Full Pipeline Execution

To run the complete pipeline from raw data to final figures:

```bash
python code/main_reproducible.py
```

This script will:
1. Download *E. coli* sequences and metadata from NCBI
2. Process sequences to extract SNPs, genes, and CNVs
3. Build the feature matrix and phylogenetic tree
4. Train and evaluate models with phylogenetically-blocked CV
5. Perform permutation testing and sensitivity analysis
6. Generate all visualizations
7. Verify artifact checksums

### Individual Pipeline Stages

You can also run individual stages:

#### 1. Data Ingestion
```bash
# Download sequences from NCBI
python code/01_ingest/download_ncbi.py

# Ingest and clean metadata
python code/01_ingest/ingest_metadata.py

# Download CARD resistance gene data
python code/01_ingest/download_card.py
```

#### 2. Feature Extraction
```bash
# Run SNP calling (requires Snippy)
bash code/02_process/run_snippy.sh

# Run resistance gene detection (requires ARIBA)
bash code/02_process/run_ariba.sh

# Build feature matrix
python code/02_process/build_feature_matrix.py

# Generate phylogenetic tree
python code/02_process/generate_phylogeny.py
```

#### 3. Model Training
```bash
# Apply mechanism-blind filtering
python code/03_model/mechanism_blind_filter.py

# Split data with phylogenetic blocking
python code/03_model/split_data.py

# Train models
python code/03_model/train_models.py

# Evaluate models
python code/03_model/evaluate.py

# Save model artifacts
python code/03_model/save_models.py
```

#### 4. Validation
```bash
# Phylogenetic permutation testing
python code/validate/phylo_permutation.py

# Sensitivity analysis
python code/04_validate/sensitivity_analysis.py
```

#### 5. Visualization
```bash
python code/05_viz/generate_plots.py
```

## Configuration

Create a `config.yaml` file in the project root to customize:

```yaml
# Maximum number of isolates to process
MAX_ISOLATES: 1000

# Random seed for reproducibility
RANDOM_SEED: 42

# NCBI BioProject IDs to download
BIO_PROJECT_IDS:
 - PRJNA123456
 - PRJNA789012

# Paths (relative to project root)
PATHS:
 RAW_DATA: data/raw
 PROCESSED_DATA: data/processed
 MODELS: data/models
 FIGURES: figures
```

## Output Files

After successful execution, you will find:

- `data/processed/feature_matrix.csv`: Combined feature matrix with SNPs, genes, and CNVs
- `data/processed/phylogeny_tree.newick`: Phylogenetic tree in Newick format
- `data/models/`: Trained model artifacts and evaluation metrics
- `data/processed/permutation_results.json`: Statistical significance results
- `figures/`: ROC curves, precision-recall curves, and feature importance plots

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Contract tests validate data schemas, while unit tests verify individual components.

## Reproducibility

This project follows the "Single Source of Truth" principle:

- All data transformations are logged and versioned
- Artifact hashes are computed and stored in `state/state.json`
- The `main_reproducible.py` script can re-execute the entire pipeline
- Configuration is centralized in `config.yaml`

## Limitations

- Requires computational resources for large-scale sequence processing
- Dependent on NCBI E-utilities rate limits
- Phylogenetic analysis requires sufficient sequence diversity
- Mechanism-blind filtering relies on accurate CARD database annotations

## Contributing

1. Create a feature branch
2. Implement changes following existing code style (black, ruff)
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NCBI for providing genomic data access
- CARD database for resistance gene annotations
- DendroPy for phylogenetic analysis capabilities
- scikit-learn for machine learning infrastructure
