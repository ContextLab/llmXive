# Quickstart Guide: Predicting Gene Essentiality from Protein Interaction Network Topology

This guide provides exact reproduction steps to run the full pipeline, from environment setup to result verification.

## Prerequisites

- Python 3.11+
- pip
- Access to the internet (for data fetching)
- 16GB+ RAM recommended (for full graph centrality calculations)

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python3.11 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install project dependencies
pip install -r requirements.txt
```

## 2. Data Fetching

The pipeline requires three main data sources:
1. **Phylogenetic Tree**: Fetched from OpenTree of Life.
2. **PPI Networks**: Fetched from STRING database.
3. **Essentiality Labels**: Fetched from DEG database.

Run the dedicated data fetching scripts to populate `data/`:

```bash
# Fetch the phylogenetic tree (Prerequisite for US2)
python code/fetch_phylogeny.py

# Fetch PPI networks and essentiality labels for all configured organisms
python code/data_loader.py
```

**Note**: If any fetch fails, the script will raise an error and stop. Do not proceed with synthetic data.

## 3. Pipeline Execution

Run the main analysis pipeline. This will:
- Compute centrality metrics (Degree, Betweenness, Eigenvector).
- Calculate Spearman correlations with essentiality labels.
- Run null models (Label Permutation & Graph Rewiring).
- Perform Phylogenetic Generalized Least Squares (PGLS) analysis.
- Generate a sensitivity report.

```bash
python code/main.py
```

**Configuration**: Edit `config.yaml` to change confidence thresholds or organism lists if needed.

## 4. Reproducibility Verification

To verify the integrity of the generated artifacts:

```bash
# Compute hashes for data and results and update state
python code/hash_checker.py
```

Check `state/hashes.yaml` to ensure all expected files are present and unchanged.

## 5. Expected Outputs

After successful execution, the following files should exist:

- `results/correlations.json`: Spearman correlations and empirical p-values.
- `results/pgls_results.json`: PGLS statistics and Benjamini-Hochberg corrected p-values.
- `results/sensitivity_report.md`: Stability analysis across confidence thresholds.
- `results/null_distribution/`: Per-organism null model data.

## Troubleshooting

- **Network Errors**: Ensure your firewall allows connections to `string-db.org`, `ftp.ncbi.nlm.nih.gov`, and `opentree.org`.
- **Memory Errors**: If `compute_betweenness_centrality` fails on large networks, check that `config.yaml` has `use_sampling: true` for networks >5,000 nodes.
- **Missing Tree**: If `results/pgls_results.json` is missing, verify `data/phylogeny/tree.newick` exists and is valid.
