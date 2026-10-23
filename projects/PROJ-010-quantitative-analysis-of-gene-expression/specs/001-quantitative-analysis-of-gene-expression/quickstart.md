# Quickstart: Gene Expression Dynamics Pipeline

## Prerequisites
```bash
# Create a clean Python 3.11 environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes scanpy, harmonypy, arboreto, pyscenic, scvelo, pandas, pyyaml, pytest, datasets, requests, tqdm
```

## Execution Workflow

### 0. Project Initialization – Download Raw Data
```bash
python src/data_pipeline/setup_data.py \
    --seed 42 \
    --output_dir data/raw
```
*Streams the Recount3 brain subset from the verified 🤗 hub, writes raw count matrix and metadata, and records SHA‑256 checksums.*

### 1. QC, Normalization & Batch Correction
```bash
python src/data_pipeline/preprocess.py \
    --input_dir data/raw \
    --output data/processed/integrated_atlas.h5ad \
    --seed 42
```
*Filters low‑quality samples, normalizes counts (CPM + log1p), selects HVGs, applies Harmony batch correction, computes LISI, and aborts if LISI < 1.2.*

### 2. Define Observed Developmental Windows
```bash
python src/network_inference/define_windows.py \
    --adata data/processed/integrated_atlas.h5ad \
    --window_config configs/windows.yaml \
    --output data/processed/windows.yaml
```
*Bins samples into age windows (e.g., 12‑16 w, 16‑20 w, Adult) and checks for ≥ 10 cells per window.*

### 3. GRN Inference & Motif Validation (per window)
```bash
for stage in $(cat data/processed/windows.yaml | yq '.stages[].stage_id' -r); do
    python src/network_inference/infer_grn.py \
        --adata data/processed/integrated_atlas.h5ad \
        --stage $stage \
        --output data/processed/networks/${stage}.json

    python src/network_inference/motif_enrichment.py \
        --network data/processed/networks/${stage}.json \
        --output data/processed/networks_motif/${stage}.json
done
```
*GRNBoost2 builds TF‑target scores; pySCENIC filters edges lacking motif support.*

### 4. Rewiring Detection & Sensitivity Sweep
```bash
python src/network_inference/rewiring.py \
    --networks_dir data/processed/networks_motif \
    --thresholds 0.01 0.05 0.1 \
    --output data/processed/rewiring_events.csv
```
*Computes z‑score‑normalized edge‑weight deltas between adjacent windows, hub‑stability scores, and records results for each threshold.*

### 5. GWAS Enrichment & Permutation Testing
```bash
python src/clinical_analysis/gwas_mapping.py \
    --gwas_url https://www.ebi.ac.uk/gwas/ \
    --output data/processed/gwas_risk_genes.json

python src/clinical_analysis/enrichment.py \
    --rewiring data/processed/rewiring_events.csv \
    --gwas data/processed/gwas_risk_genes.json \
    --permutations 5000 \
    --output data/processed/disorder_enrichment.csv
```
*Creates matched‑gene backgrounds, runs hypergeometric tests, applies Benjamini‑Hochberg correction, and performs ≥ 5 000 permutations.*

### 6. Independent Validation (if open cohort available)
```bash
python src/clinical_analysis/validation.py \
    --primary data/processed/disorder_enrichment.csv \
    --validation_cohort data/external/psychencode_fetal.h5ad \
    --output data/processed/disorder_enrichment_validated.csv
```
*Replicates enrichment in an independent scRNA‑seq cohort; adds `is_validated` flag.*

### 7. Visualization
```bash
python src/network_inference/plotting.py \
    --rewiring data/processed/rewiring_events.csv \
    --networks_dir data/processed/networks_motif \
    --output_dir figures/
```
*Generates Plotly HTML network visualizations and Cytoscape `.cx` files.*

### 8. Run End‑to‑End Test
```bash
pytest -m integration
```
*Executes `tests/integration/test_end_to_end.py`, which validates that all output files conform to the schemas in `contracts/`.*

---
