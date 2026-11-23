# Quickstart: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

## Prerequisites

- Python 3.11+
- `mafft` and `fasttree` binaries installed in system PATH.
- Internet access for NCBI/KEGG API calls.
- ~7 GB RAM, ~14 GB disk.

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-408-investigating-the-predictive-power-of-pl
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Binaries**:
    ```bash
    mafft --version
    fasttree -version
    ```

## Running the Pipeline

### 1. Download Data
Run the data loader to fetch sequences and metabolite profiles.
```bash
python code/main.py --step download --species-list data/species_list.csv
```
*Note: `species_list.csv` must contain columns: `ncbi_tax_id`, `kegg_code`, `species_name`.*

### 2. Build Phylogeny
Align sequences and build the tree.
```bash
python code/main.py --step phylogeny
```

### 3. Compute Distances & Test
Calculate matrices and run Mantel tests (including Spearman robustness check).
```bash
python code/main.py --step stats
```

### 4. Generate Visuals
Create plots and summary report.
```bash
python code/main.py --step viz
```

## Expected Outputs

- `output/results/mantel_stats.json`: Contains `r`, `p_value`, `spearman_r`, `spearman_p_value`, `partial_r`, `partial_p_value`.
- `output/figures/phylo_metabolite_heatmap.png`: Tree with metabolite overlay.
- `output/figures/mantel_results.png`: Scatter plot and permutation histogram.
- `output/reports/analysis_summary.txt`: Human-readable summary.

## Troubleshooting

- **API Rate Limit**: If `Entrez` fails, wait 1 minute and retry. The script implements exponential backoff.
- **Missing Data**: If >20% species are missing, the script will exit with error code 1 and list missing IDs.
- **Memory Error**: If alignment fails due to RAM, reduce the species list or increase swap space (not recommended for CI).