# Quickstart: Gene Expression Dynamics Pipeline

## Prerequisites
```bash
# Create a clean Python 3.11 environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes scanpy, harmonypy, arboreto, pyscenic, monocle3, pandas, pyyaml, pytest, datasets, requests, tqdm
```

## Execution Workflow

### 0. Project Initialization – Download Raw Data
```bash
python src/data_pipeline/setup_data.py \
    --seed 42 \
    --output_dir data/raw
```
*Streams the Human Cell Atlas brain single‑cell dataset from the verified 🤗 hub, writes raw count matrix and metadata, and records cryptographic checksums. The script aborts if any checksum mismatch is detected, guaranteeing deterministic acquisition.*

### 1. QC, Normalization & Batch Correction
```bash
python src/data_pipeline/preprocess.py \
    --input_dir data/raw \
    --output data/processed/integrated_atlas.h5ad \
    --seed 42
```
*Filters low‑quality samples (≥ 200 genes per cell, genes expressed in ≥ 3 cells), normalizes counts (CPM + log1p), selects HVGs, applies Harmony **with age‑preserving safeguard** (checks donor‑age correlation, adds `age` as covariate when |r| > 0.3), computes LISI, and aborts if LISI < 1.2.*

### 2. Generate Dataset Summary (Contract Validation)
```bash
python src/data_pipeline/summarize_dataset.py \
    --adata data/processed/integrated_atlas.h5ad \
    --output data/processed/dataset_summary.json
```
*Writes a JSON file conforming to `contracts/dataset.schema.yaml` (cells, genes, and generic metadata).*

### 3. Define Observed Developmental Windows
```bash
python src/network_inference/define_windows.py \
    --adata data/processed/integrated_atlas.h5ad \
    --config configs/windows.yaml \
    --output data/processed/windows.yaml
```
*Bins samples into age windows (e.g., 12‑16 w, 16‑20 w, Adult) and checks for ≥ 10 cells per window.*

### 4. Compute Pseudotime and Sliding Windows Within Each Age Window
```bash
python src/network_inference/infer_pseudotime.py \
    --adata data/processed/integrated_atlas.h5ad \
    --windows data/processed/windows.yaml \
    --output data/processed/pseudotime_windows.yaml
```
*Runs Monocle3 pseudotime inference per age window and creates overlapping sliding windows (≥ 200 cells each).*

### 5. GRN Inference & Motif Validation (per pseudotime window)
```bash
for pw in $(cat data/processed/pseudotime_windows.yaml | yq '.windows[].window_id' -r); do
    python src/network_inference/infer_grn.py \
        --adata data/processed/integrated_atlas.h5ad \
        --window $pw \
        --output data/processed/networks/${pw}.json

    python src/network_inference/motif_enrichment.py \
        --network data/processed/networks/${pw}.json \
        --output data/processed/networks_motif/${pw}.json
done
```
*GRNBoost2 builds TF‑target scores; pySCENIC filters edges lacking motif support.*

### 6. Rewiring Detection & Sensitivity Sweep
```bash
python src/network_inference/rewiring.py \
    --networks_dir data/processed/networks_motif \
    --thresholds 0.01 0.05 0.1 \
    --output data/processed/rewiring_events.csv
```
*Computes z‑score‑normalized edge‑weight deltas between adjacent pseudotime windows, hub‑stability scores, and records results for each threshold.*

### 7. GWAS Enrichment & Permutation Testing
```bash
# The risk‑gene list is a static file bundled with the repository
python src/clinical_analysis/enrichment.py \
    --rewiring data/processed/rewiring_events.csv \
    --gwas data/externals/gwas_risk_genes.json \
    --permutations 5000 \
    --output data/processed/disorder_enrichment.csv
```
*Creates matched‑gene backgrounds, runs hypergeometric tests, applies Benjamini‑Hochberg correction, and performs ≥ 5 000 permutations.*

### 8. Independent Validation (if open bulk cohort available)
```bash
python src/clinical_analysis/validation.py \
    --primary data/processed/disorder_enrichment.csv \
    --validation_cohort data/external/bulk_brain_agecourse.h5ad \
    --output data/processed/disorder_enrichment_validated.csv
```
*Replicates enrichment in an independent bulk RNA‑seq age course; adds `is_validated` flag.*

### 9. Visualization
```bash
python src/network_inference/plotting.py \
    --rewiring data/processed/rewiring_events.csv \
    --networks_dir data/processed/networks_motif \
    --output_dir figures/
```
*Generates Plotly HTML network visualizations and Cytoscape `.cx` files.*

### 10. Run End‑to‑End Test
```bash
pytest -m integration
```
*Executes `tests/integration/test_end_to_end.py`, which validates that all output files conform to the schemas in `contracts/`.*

---


