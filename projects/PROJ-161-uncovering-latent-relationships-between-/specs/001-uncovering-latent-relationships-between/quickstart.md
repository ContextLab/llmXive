# Quickstart: Uncovering Latent Relationships Between Antibiotic Descriptors

## Prerequisites
- Python 3.11+
- pip
- 7 GB+ RAM, 14 GB+ Disk
- Internet access (for data fetch)

## 1. Environment Setup

```bash
# Clone and enter project
cd projects/PROJ-161-uncovering-latent-relationships-between-
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Fetching (Phase 0)
The pipeline automatically fetches data. For the first run:

```bash
# Run the download script (Live Fetch)
python src/data/download.py --mode full
```
*Note: If NCBI FTP is unreachable, the script will log a warning and exit with `DATA_SOURCE_UNAVAILABLE`. No synthetic data is generated.*

## 3. Running the Pipeline (Phase 1)

Execute the full analysis:

```bash
python src/main.py
```

This will:
1. Canonicalize SMILES and calculate descriptors (RDKit).
2. Merge with resistance data (NCBI) with aggregation.
3. Run UMAP and DBSCAN.
4. Perform statistical tests (Mann-Whitney, Fisher's).
5. Generate plots and final reports.

### Reproducibility Test
To verify reproducibility (SC-005), run the pipeline with a cached snapshot:

```bash
# First, generate a snapshot (run once)
python src/main.py --save-snapshot data/raw/snapshot/

# Then run the test (uses cached data)
python src/main.py --data-snapshot data/raw/snapshot/
```

## 4. Verifying Results

Check the output directory:

```bash
ls data/processed/
# Expected: merged_compounds.parquet, final_ranking.csv, umap_plot.png, merge_metrics.json, runtime_metrics.json
```

Run unit tests:

```bash
pytest tests/unit/ -v
```

Run integration tests (reproducibility):

```bash
pytest tests/integration/test_pipeline.py -v
```

## 5. Troubleshooting
- **Memory Error**: Reduce the dataset size in `config.py` (e.g., `MAX_COMPOUNDS=5000`).
- **NCBI Timeout**: The script has exponential backoff. If it fails after 5 retries, it logs `DATA_SOURCE_UNAVAILABLE`.
- **No Clusters Found**: Check `data/processed/clustering_results.csv` for `cluster_id=-1` (noise). Adjust `eps` in `config.py`.
- **Reproducibility Fail**: Ensure `--data-snapshot` is used for the test run to guarantee identical input data.

