# Quickstart Guide: Predicting Gene Essentiality from Protein Interaction Network Topology

This guide provides exact reproduction steps to run the full pipeline from scratch, ensuring reproducibility of results as per Constitution Principle I.

## Prerequisites

- Python 3.11+
- pip
- 14GB+ free disk space (for data and results)
- 8GB+ RAM (streaming mode enabled for large datasets)

## 1. Environment Setup

Clone the repository and set up the virtual environment:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Project Structure Initialization

Ensure the required directory structure exists:

```bash
bash scripts/init_project_structure.sh
```

This creates: `code/`, `data/raw/`, `data/processed/`, `data/phylogeny/`, `results/`, `tests/`.

## 3. Data Fetching

The pipeline automatically fetches required data. [UNRESOLVED-CLAIM: c_5d16e472 — status=not_enough_info] Ensure you have internet access.

### 3.1 Phylogenetic Tree
The tree is fetched from OpenTree of Life for the 7 model organisms. [UNRESOLVED-CLAIM: c_706d82b2 — status=not_enough_info]
Tax IDs: 9606, 10090, 7955, 6239, 7227, 8355, 9615. [UNRESOLVED-CLAIM: c_0b1e4846 — status=not_enough_info]
Output: `data/phylogeny/tree.newick`

```bash
python code/fetch_phylogeny.py
```

**Note**: If this fails, the build halts immediately. Do not proceed without a valid tree.

### 3.2 PPI Networks and Essentiality Labels
The main pipeline script handles fetching of STRING PPI networks and DEG essentiality labels. [UNRESOLVED-CLAIM: c_fd9f9e6f — status=not_enough_info]

## 4. Pipeline Execution

Run the full analysis for all configured organisms:

```bash
python code/main.py
```

This executes:
1. **Data Loading**: Fetches PPI networks (STRING) and essentiality labels (DEG).
2. **ID Mapping**: Aligns identifiers via Ensembl BioMart.
3. **Network Analysis**: Computes degree, betweenness, and eigenvector centralities.
4. **Statistical Analysis**: Calculates Spearman correlations and empirical p-values via label permutation.
5. **Null Models**: Generates rewired graphs and computes rewired correlations.
6. **Comparative Analysis**: Runs PGLS with Fisher's z-transformation and Benjamini-Hochberg correction.
7. **Sensitivity Analysis**: Re-runs correlation analysis across confidence thresholds [500, 700, 900].

**Expected Runtime**: ~2-4 hours depending on network sizes and available CPU.

## 5. Output Verification

Upon successful completion, the following artifacts should exist:

- `results/correlations.json`: Spearman ρ, p-values, and empirical p-values for all organisms.
- `results/null_distribution/{organism}/threshold_{value}/label_permutation.csv`: Permutation results.
- `results/null_distribution/{organism}/threshold_{value}/rewired_correlations.csv`: Rewired null model results.
- `results/pgls_results.json`: PGLS statistics and BH-corrected p-values.
- `results/sensitivity_report.md`: Stability analysis across confidence thresholds.
- `state/hashes.yaml`: SHA256 hashes of all data and results for reproducibility verification.

Verify the existence of key files:

```bash
ls -lh results/correlations.json
ls -lh results/pgls_results.json
ls -lh results/sensitivity_report.md
ls -lh data/phylogeny/tree.newick
```

## 6. Reproducibility Verification

To verify reproducibility, re-run the pipeline and compare hashes:

```bash
# Run pipeline again
python code/main.py

# Compute and update hashes
python code/hash_checker.py

# Verify hashes match previous run
cat state/hashes.yaml
```

The hashes in `state/hashes.yaml` should remain identical across runs (assuming identical input data versions).

## 7. Troubleshooting

- **API Rate Limits**: The pipeline implements exponential backoff for API calls. If you hit rate limits, wait and retry.
- **Memory Errors**: For large networks, betweenness centrality uses k-sampling. Ensure `config.yaml` has appropriate settings.
- **Missing Data**: If a specific organism's data is missing, the pipeline logs a warning and skips that organism, continuing with others.
- **Disconnected Networks**: If a network has no edges, centrality is assigned as 0 and a warning is logged.

## 8. Running Specific Components

To run analysis for a single organism (e.g., *S. cerevisiae*):

```bash
python -c "from code.main import run_pipeline_for_organism; run_pipeline_for_organism('S. cerevisiae', 700)"
```

To run sensitivity analysis only:

```bash
python -c "from code.main import run_sensitivity_analysis; run_sensitivity_analysis('S. cerevisiae')"
```

## 9. Testing

Run the test suite:

```bash
pytest tests/ -v
```

This includes contract tests for JSON schemas and integration tests for pipeline components.

## 10. Configuration

Edit `config.yaml` to modify:
- Organism list
- Confidence thresholds for STRING data
- Paths to data directories
- Number of permutations for null models

Default configuration is suitable for most use cases.
