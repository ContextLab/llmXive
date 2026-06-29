# Quickstart: 001-soil-microbiome-diversity-disease-resistance

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker (for QIIME 2/CoNet containerization, optional)
- Git (for version control)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd projects/PROJ-136-investigating-the-impact-of-soil-microbi
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r code/requirements.txt
```

Expected dependencies (per code/requirements.txt):
- pandas
- numpy
- scipy
- scikit-learn
- statsmodels
- biopython
- networkx
- pytest
- pyyaml

### 4. Verify Installation

```bash
python -c "import pandas; import statsmodels; import networkx; print('All dependencies installed successfully')"
```

## Data Acquisition

### **PAUSE: DATASETS UNAVAILABLE**

**IMPORTANT**: Per research.md, the verified datasets block contains NO verified sources for EMP agricultural subset, MG-RAST soil microbiome, or plant disease incidence records.

**DO NOT PROCEED** until one of the following is completed:

1. **Option A**: Locate and verify alternative datasets containing required variables (OTU/ASV tables with plant species, GPS, soil type, sequencing depth; disease incidence with sample ID, disease type, incidence rate, measurement date)
2. **Option B**: Amend the spec to reference available datasets that contain subset of required variables
3. **Option C**: Flag as blocking gap requiring spec revision

If datasets become verified and available:

```bash
python code/analysis/data_acquisition.py --source emp --output data/raw/emp_agricultural.csv
python code/analysis/data_acquisition.py --source mg-rast --output data/raw/mg-rast_soil.csv
python code/analysis/data_acquisition.py --source disease --output data/raw/disease_incidence.csv
```

### Step 2: Compute Checksums

```bash
python code/analysis/data_acquisition.py --checksum --input data/raw/ --output state/PROJ-136-artifact-hashes.json
```

## Preprocessing

```bash
python code/analysis/preprocessing.py --input data/raw/ --output data/processed/ --rarefaction-depth 10000
```

This will:
- Filter OTU/ASV tables to retain taxa present in ≥5% of samples
- Rarefy to uniform sequencing depth (10k reads per sample)
- Align disease incidence data with soil samples via location and date fields

## Analysis

### Step 1: Compute Alpha-Diversity

```bash
python code/analysis/diversity_analysis.py --input data/processed/filtered_otu_table.csv --output data/processed/diversity_metrics.csv
```

### Step 2: Fit Statistical Models

```bash
python code/analysis/statistical_models.py --input data/processed/diversity_metrics.csv --output results/model_results.json
```

### Step 3: Run Permutation Tests

```bash
python code/analysis/permutation_tests.py --input data/processed/diversity_metrics.csv --permutations 10000 --output results/permutation_results.json
```

### Step 4: ANCOM Differential Abundance

```bash
python code/analysis/keystone_taxa.py --input data/processed/filtered_otu_table.csv --disease-cutoff median --output results/ancom_results.json
```

### Step 5: Co-occurrence Network

```bash
python code/analysis/keystone_taxa.py --network --input data/processed/filtered_otu_table.csv --output results/network_analysis.json
```

## Testing

### Run All Tests

```bash
pytest code/tests/ -v
```

### Run Contract Tests

```bash
pytest code/tests/contract/ -v
```

### Run Integration Tests

```bash
pytest code/tests/integration/ -v
```

## Output

Expected outputs in `results/`:

- `model_results.json`: Beta regression/GLMM coefficients, p-values, effect sizes
- `permutation_results.json`: Permutation test p-values, stability metrics
- `ancom_results.json`: Differential abundance q-values, enriched taxa
- `network_analysis.json`: Co-occurrence network centrality metrics, keystone taxa

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model convergence failure | Check sample size; try alternative model specifications; report as limitation |
| ANCOM no significant taxa | Report as null result; do NOT fabricate findings |
| Dataset variables missing | Record [MISSING_VARIABLE: <variable-name>] per FR-008 |
| Memory error | Sample data to fit 7 GB RAM constraint; document sampling rate |
| QIIME 2 not available | Fall back to scikit-bio diversity calculations |
| **PAUSE: Datasets unavailable** | Do not proceed until research.md FATAL MISMATCH is resolved via Option A/B/C |