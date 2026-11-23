# Quickstart Guide: Microbial Community Succession Pipeline

This guide walks you through setting up and running the pipeline to analyze microbial succession in constructed wetlands.

## Step 1: Environment Setup

Ensure you have Python 3.11+ installed.

```bash
# Navigate to project root
cd projects/PROJ-280-investigating-microbial-community-succes

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Verify Project Structure

Run the setup scripts to ensure all directories exist.

```bash
python code/setup_project.py
python code/setup_subdirectories.py
```

Verify the structure:
```bash
tree -L 2.
```
Expected directories: `data/raw`, `data/processed`, `data/config`, `code`, `tests`, `state`.

## Step 3: Configure Datasets

Edit `data/config/dataset_ids.json` to include verified public datasets.

Example:
```json
{
 "datasets": [
 {
 "id": "zenodo_constructed_wetland_16s",
 "source": "Zenodo",
 "url": ""
 }
 ]
}
```
*Note: Replace the URL with a real, accessible dataset containing constructed wetland 16S data with nutrient removal metadata.*

Validate the configuration:
```bash
python code/validators.py
```

## Step 4: Run the Pipeline

Execute the pipeline stages in order. Each stage writes to `data/processed/`.

### 4.1 Retrieve Data
```bash
python code/01_retrieve_data.py
```
- Downloads raw data to `data/raw/`.
- Halts with "CRITICAL DATA GAP" if validation fails.

### 4.2 Preprocess Data
```bash
python code/02_preprocess.py
```
- Filters for constructed wetlands.
- Subsamples to uniform depth.
- Generates `robustness_verification_report.json`.
- Halts if sample count < 30.

### 4.3 Diversity Analysis
```bash
python code/03_diversity.py
```
- Calculates Shannon/Simpson indices.
- Runs PERMANOVA with FDR correction.
- Generates `power_analysis_report.json`.
- Halts if power < 0.8.

### 4.4 Network Analysis
```bash
python code/04_network.py
```
- Constructs co-occurrence networks.
- Calculates modularity and sensitivity.
- Generates `network_sensitivity_report.json`.

### 4.5 Correlation Analysis
```bash
python code/05_correlation.py
```
- Correlates taxa with nutrient removal rates.
- Checks VIF for collinearity.
- Generates `correlation_results.json`.

### 4.6 Record Checksums
```bash
python code/06_checksum_recorder.py
```
- Updates `state/projects/PROJ-280-investigating-microbial-community-succes.yaml`.

## Step 5: Inspect Results

Check the generated reports in `data/processed/`:
- `diversity_metrics.json`: Diversity metrics and PERMANOVA results.
- `correlation_results.json`: Significant taxa-nutrient correlations.
- `network_analysis.json`: Network topology.

## Step 6: Run Tests

Validate the pipeline implementation:
```bash
pytest tests/contract/
pytest tests/integration/
```

## Troubleshooting

- **Error: "CRITICAL DATA GAP"**: Check `data/config/dataset_ids.json` for valid URLs and sources.
- **Error: "UNDERPOWERED"**: The dataset has too few samples for robust statistical testing.
- **Error: Module not found**: Ensure you are running from the project root and dependencies are installed.