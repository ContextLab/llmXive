# Quickstart Guide: Predicting Gene Essentiality from Protein Interaction Network Topology

This guide provides exact steps to reproduce the full analysis pipeline for predicting gene essentiality using protein-protein interaction (PPI) network topology.

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Access to the internet (for fetching data from STRING, DEG, and OpenTree APIs)
- At least 14GB disk space and 7GB RAM (for full dataset processing)

## 1. Environment Setup

### Clone and Install Dependencies

```bash
# Ensure you are in the project root directory
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import networkx, pandas, scipy, statsmodels, requests, pyyaml, numpy, Bio; print('All dependencies installed successfully.')"
```

## 2. Project Structure Initialization

Run the initialization script to create the required directory structure:

```bash
bash scripts/init_project_structure.sh
```

This creates:
- `code/` - Source code
- `data/raw/` - Raw downloaded data
- `data/processed/` - Processed data
- `data/phylogeny/` - Phylogenetic tree data
- `results/` - Analysis outputs
- `tests/` - Test suites

## 3. Data Fetching

The pipeline automatically fetches real data from external sources. No manual download is required.

### Phylogenetic Tree (Hard Prerequisite)

The phylogenetic tree is fetched from OpenTree of Life. This step MUST succeed before any analysis can proceed.

```bash
python code/fetch_phylogeny.py
```

**Output**: `data/phylogeny/tree.newick`

**Failure Condition**: If this script fails, the entire pipeline will abort. Do not proceed until this file exists.

### PPI Networks and Essentiality Labels

The main pipeline script will automatically fetch:
- PPI networks from STRING API (confidence ≥ 700)
- Essentiality labels from DEG database

## 4. Pipeline Execution

### Full Analysis Run

Execute the complete pipeline for all model organisms:

```bash
python code/main.py
```

This will:
1. Fetch PPI networks for each organism
2. Fetch essentiality labels
3. Map gene identifiers
4. Compute centrality metrics (degree, betweenness, eigenvector)
5. Calculate Spearman correlations
6. Run null models (label permutation and graph rewiring)
7. Perform PGLS statistical testing
8. Generate sensitivity analysis report

### Organism-Specific Run

To run analysis for a single organism:

```bash
python code/main.py --organism saccharomyces_cerevisiae --threshold 700
```

### Sensitivity Analysis

Run sensitivity analysis across confidence thresholds:

```bash
python code/main.py --sensitivity
```

## 5. Output Files

After successful execution, the following files will be generated:

- `results/correlations.json` - Spearman correlations and empirical p-values for each organism
- `results/pgls_results.json` - Phylogenetic Generalized Least Squares results with Benjamini-Hochberg corrected p-values
- `results/sensitivity_report.md` - Markdown report of stability analysis across thresholds
- `results/null_distribution/{organism}/threshold_<value>/` - Null model results (label permutation and graph rewiring)

## 6. Reproducibility Verification

### Hash Verification

Verify data integrity using the hash checker:

```bash
python code/hash_checker.py
```

This updates `state/hashes.yaml` with SHA256 checksums of all data and result files.

### Contract Tests

Validate output schemas:

```bash
pytest tests/contract/ -v
```

### Integration Tests

Run integration tests with mock data:

```bash
pytest tests/integration/ -v
```

## 7. Troubleshooting

### API Rate Limiting

If you encounter rate limiting errors:
- Add a small delay between requests (handled automatically by `exponential_backoff` in `utils.py`)
- Consider running analysis for fewer organisms simultaneously

### Memory Issues

For large networks (>5,000 nodes):
- The pipeline automatically uses k-sampling for betweenness centrality
- Ensure you have at least 7GB RAM available

### Missing Data

If the phylogenetic tree cannot be fetched:
- Verify internet connectivity
- Check OpenTree API status
- The pipeline will fail immediately (no fallback to synthetic data)

## 8. Configuration

Modify `config.yaml` to adjust:
- Organism IDs
- Confidence thresholds
- File paths
- Logging levels

Example configuration:
```yaml
organisms:
 - saccharomyces_cerevisiae
 - homo_sapiens
 - mus_musculus
confidence_thresholds:
 - 500
 - 700
 - 900
```

## 9. Performance Notes

- Expected runtime: < 6 hours on standard hardware
- Betweenness centrality uses sampling for large networks
- Parallel processing available for null model generation

## 10. Support

For issues or questions, refer to:
- `research.md` for detailed methodology
- `specs/` directory for feature specifications
- `tests/` directory for test coverage

---
*Last updated: Generated for project PROJ-452-predicting-gene-essentiality-from-protei*
