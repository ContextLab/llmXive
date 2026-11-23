# Quickstart Guide: Predicting Gene Essentiality from Protein Interaction Network Topology

This guide provides the exact steps to set up the environment, fetch real data, run the analysis pipeline, and verify reproducibility.

## 1. Environment Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)
- Access to the internet (for data fetching)

### Installation
```bash
# Clone the repository (if not already done)
git clone <repo-url>
cd PROJ-452-predicting-gene-essentiality-from-protei

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

Ensure `code/config.py` contains the correct organism IDs and thresholds.
The default configuration includes:
- Organisms: Human (9606), S. cerevisiae (559292), E. coli (83333), Mouse (10090), D. melanogaster (7227)
- Confidence Thresholds: 500, 700, 900
- Random Seed: 42

You can modify `code/config.py` or the associated YAML config file if needed.

## 3. Data Fetching

The pipeline automatically fetches data from the following real sources during execution:
- **STRING API**: Protein-Protein Interaction (PPI) networks.
- **DEG Database**: Gene essentiality labels (via FTP/API).
- **OpenTree of Life**: Phylogenetic tree for comparative analysis.
- **Ensembl BioMart**: Gene ID mapping.

No manual download is required. The pipeline will fetch data on first run.

## 4. Pipeline Execution

Run the full analysis pipeline:
```bash
python code/main.py
```

To run a dry-run (data fetching and mapping only, no analysis):
```bash
python code/main.py --dry-run
```

To run with a specific organism (optional, for debugging):
```bash
python code/main.py --organism 559292
```

### Expected Outputs
After successful execution, the following files will be generated in the `results/` directory:
- `results/correlations.json`: Spearman correlations and p-values.
- `results/pgls_results.json`: Phylogenetic Generalized Least Squares results.
- `results/sensitivity_report.md`: Sensitivity analysis report.
- `results/sensitivity_summary.json`: Summary of sensitivity analysis.
- `results/mapping_coverage.json`: ID mapping statistics.
- `results/topology_validation.json`: Scale-free topology validation.
- `state/projects/PROJ-452-...yaml`: Hash state for reproducibility.

## 5. Reproducibility Verification

To verify reproducibility, run the pipeline again and compare the output hashes:
```bash
python code/hash_checker.py
```

The `state/` directory will be updated with the SHA256 hashes of all generated files. Compare these hashes with previous runs to ensure consistency.

## 6. Troubleshooting

If you encounter errors during execution, refer to the sections below.

### Data Fetching Errors (T073, T074, T075)

**Error Code: `DataFetchError`**
- **Log Message**: "Failed to fetch data for organism {organism_id}: {error_code}"
- **Cause**: The primary data source (STRING API, DEG FTP, Ensembl BioMart) is unreachable or returned an error.
- **Resolution Steps**:
 1. Check your internet connection.
 2. Verify the organism ID in `code/config.py` is correct.
 3. Check the status of the external APIs (STRING, DEG, Ensembl).
 4. If the error persists, the pipeline will skip the affected organism and log a warning. No synthetic data is used.

**Error Code: `IDMappingError`**
- **Log Message**: "ID mapping failed for organism {organism_id}: {error_message}"
- **Cause**: Ensembl BioMart failed to map gene IDs, and the fallback strategy (Gene Symbol) also failed.
- **Resolution Steps**:
 1. Ensure the Ensembl BioMart endpoint is accessible.
 2. Check if the organism has a valid Ensembl database.
 3. If mapping coverage is low (<10%), the fallback strategy will be attempted. If this also fails, the organism is skipped.

### Network Analysis Errors (T070)

**Error Code: `NetworkAnalysisError`**
- **Log Message**: "Network too sparse for organism {organism_id} at threshold {threshold}"
- **Cause**: The confidence threshold is too high, resulting in a network with <500 edges.
- **Resolution Steps**:
 1. Lower the confidence threshold in `code/config.py`.
 2. The pipeline will set centrality metrics to NaN/0 for this organism/threshold combination and record the reason in the output JSON.

### PGLS Analysis Errors (T076)

**Error Code: `PGLSModelError`**
- **Log Message**: "PGLS model failed to converge for {organism_list}"
- **Cause**: The phylogenetic tree or correlation data is insufficient for the PGLS model (e.g., small sample size, singular matrix).
- **Resolution Steps**:
 1. Verify that the phylogenetic tree (`data/phylogeny/tree.newick`) exists and contains the correct number of tips.
 2. Check if the effective sample size (number of organisms with valid data) is >= 10.
 3. If the model fails to converge, the result will be omitted from the output JSON, and a warning will be logged.

### General Errors

**Error Code: `ConfigError`**
- **Log Message**: "Configuration error: {error_message}"
- **Cause**: Invalid configuration in `code/config.py` or YAML files.
- **Resolution Steps**:
 1. Check the syntax of `code/config.py` and any associated YAML files.
 2. Ensure all required fields are present and valid.

**Error Code: `FileNotFoundError`**
- **Log Message**: "File not found: {file_path}"
- **Cause**: A required file (e.g., phylogenetic tree, config) is missing.
- **Resolution Steps**:
 1. Run the data fetching step again to ensure all necessary files are downloaded.
 2. Verify the file paths in `code/config.py`.

## 7. Support

For further assistance, please refer to the `research.md` file for detailed information on data sources and the `specs/` directory for feature specifications.