# PROJ-280: Investigating Microbial Community Succession in Constructed Wetlands

## Overview
This project implements an automated scientific pipeline to analyze microbial community succession in constructed wetlands using public 16S rRNA datasets. The pipeline retrieves, preprocesses, and analyzes community data to test hypotheses about diversity changes across wetland establishment stages (early, intermediate, mature) and their correlation with nutrient removal efficiency.

## Project Structure
```
projects/PROJ-280-investigating-microbial-community-succes/
├── data/
│ ├── raw/ # Downloaded raw datasets
│ ├── processed/ # Filtered and processed data artifacts
│ └── config/ # Configuration files (dataset IDs, parameters)
├── code/
│ ├── 01_retrieve_data.py # Data retrieval from NCBI SRA/Zenodo
│ ├── 02_preprocess.py # Filtering, subsampling, sensitivity analysis
│ ├── 03_diversity.py # Alpha/beta diversity, PERMANOVA, power analysis
│ ├── 04_network.py # Co-occurrence networks, modularity analysis
│ ├── 05_correlation.py # Taxa-nutrient correlation with VIF checks
│ ├── 06_checksum_recorder.py # Artifact integrity tracking
│ ├── data_models.py # Sample, Taxon, FeatureTable classes
│ ├── dataset_config_validator.py # JSON schema validation
│ ├── utils.py # Shared helpers (VIF, FDR, checksums)
│ ├── validators.py # Dataset config validation logic
│ └── requirements.txt # Pinned dependencies
├── tests/
│ ├── unit/ # Unit tests
│ ├── contract/ # Schema contract tests
│ └── integration/ # Integration tests
├── state/
│ └── projects/
│ └── PROJ-280-investigating-microbial-community-succes.yaml # Artifact hashes
├── contracts/
│ ├── dataset-config.schema.yaml
│ ├── feature-table.schema.yaml
│ └── output-metrics.schema.yaml
├── docs/
│ ├── README.md
│ └── quickstart.md
├──.flake8
├── pyproject.toml
└── MANIFEST.txt
```

## Prerequisites
- Python 3.11+
- pip-tools (for dependency management)
- Access to internet (for downloading public datasets)

## Installation
1. Clone the repository and navigate to the project directory.
2. Install dependencies:
 ```bash
 cd projects/PROJ-280-investigating-microbial-community-succes
 pip install -r code/requirements.txt
 ```
3. Verify project structure:
 ```bash
 python code/setup_project.py
 python code/setup_subdirectories.py
 ```

## Configuration
Before running the pipeline, configure the dataset sources in `data/config/dataset_ids.json`. This file must list verified public datasets (NCBI SRA or Zenodo) containing constructed wetland 16S data with nutrient removal metadata.

Example `dataset_ids.json`:
```json
{
 "datasets": [
 {
 "id": "example_dataset_1",
 "source": "Zenodo",
 "url": ""
 }
 ]
}
```

## Pipeline Execution
The pipeline executes in sequential stages. Each stage validates its inputs and halts with a "CRITICAL DATA GAP" or "UNDERPOWERED" error if requirements are not met.

1. **Retrieve Data**:
 ```bash
 python code/01_retrieve_data.py
 ```
 Downloads raw feature tables and metadata to `data/raw/`.

2. **Preprocess Data**:
 ```bash
 python code/02_preprocess.py
 ```
 Filters for constructed wetlands, applies minimum read depth, performs sensitivity analysis, and generates robustness reports.

3. **Diversity Analysis**:
 ```bash
 python code/03_diversity.py
 ```
 Calculates alpha/beta diversity, performs power analysis, and runs PERMANOVA tests with FDR correction.

4. **Network Analysis**:
 ```bash
 python code/04_network.py
 ```
 Constructs co-occurrence networks, calculates modularity, and performs sensitivity analysis on correlation thresholds.

5. **Correlation Analysis**:
 ```bash
 python code/05_correlation.py
 ```
 Correlates taxa abundances with nutrient removal rates, checks for collinearity (VIF), and performs cross-validation.

6. **Checksum Recording**:
 ```bash
 python code/06_checksum_recorder.py
 ```
 Records SHA256 hashes of all processed artifacts for integrity tracking.

## Output Artifacts
All outputs are stored in `data/processed/`:
- `sample_pool_validation.json`: Sample counts per stage.
- `robustness_verification_report.json`: Sensitivity analysis results for subsampling depth.
- `power_analysis_report.json`: Statistical power for PERMANOVA.
- `diversity_metrics.json`: Alpha/beta diversity and PERMANOVA results.
- `network_analysis.json`: Network topology and modularity metrics.
- `correlation_results.json`: Taxa-nutrient correlations with VIF flags.
- `exclusion_log.json`: Log of excluded samples and reasons.

## Validation & Testing
- **Contract Tests**: Validate JSON schemas for inputs and outputs.
- **Integration Tests**: Verify end-to-end pipeline stages.
- **Unit Tests**: Validate individual helper functions.

Run tests:
```bash
pytest tests/
```

## Data Integrity
The `state/projects/PROJ-280-investigating-microbial-community-succes.yaml` file tracks SHA256 hashes of all processed artifacts. Use `code/06_checksum_recorder.py` to update this state after each run.

## Troubleshooting
- **CRITICAL DATA GAP**: No valid datasets found or validation failed. Check `data/config/dataset_ids.json`.
- **UNDERPOWERED**: Sample size insufficient for statistical power (< 0.8). Increase sample count or relax effect size assumptions.
- **UNDER-DETERMINED**: Number of taxa exceeds sample size; network modularity cannot be reliably calculated.

## License
MIT License
