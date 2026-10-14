# Quickstart: Gene Expression Dynamics Pipeline

## Prerequisites
```bash
# Python 3.11
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes scanpy, harmonypy, arboreto, scvelo, pyscenic, pandas, pyyaml, pytest
```

## Execution Workflow

### 0. Project Initialization
```bash
python src/data_pipeline/setup_data.py \
    --seed 42 \
    --output_dir data/raw
```
*Creates `data/raw/` and writes a checksum manifest.*

### 1. Data Acquisition & Integration
```bash
python src/data_pipeline/preprocess.py \
    --dataset human_mtg \
    --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA" \
    --output data/processed/integrated_atlas.h5ad \
    --seed 42
```
*Downloads BICCN Human MTG dataset from verified HuggingFace source, filters, normalizes, runs Harmony, computes LISI, validates pseudotime markers, and aborts if LISI < 1.2.*

### 2. Pseudotime Ordering & Validation
```bash
python src/network_inference/pseudotime.py \
    --input data/processed/integrated_atlas.h5ad \
    --output data/processed/pseudotime.h5ad \
    --marker_genes NEUROD6,GFAP,MAP2 \
    --min_correlation 0.6 \
    --seed 42
```
*Computes pseudotime using Monocle3 (fallback Slingshot if needed). Validates correlation with developmental markers; requires Pearson r ≥ 0.6. Aborts with clear error if validation fails.*

### 3. Sliding‑Window GRN Inference
```bash
python src/network_inference/infer_grn.py \
    --input data/processed/pseudotime.h5ad \
    --windows 5 \
    --hub_degree_threshold 10 \
    --hub_top_n 20 \
    --output_dir data/processed/networks \
    --seed 42
```
*Produces `{stage_id}.json` network files. Hubs are defined as TFs with degree ≥ 10, or top 20 TFs if fewer than 20 meet threshold.*

### 4. Motif Enrichment Validation (Mandatory)
```bash
python src/network_inference/motif_enrichment.py \
    --network_dir data/processed/networks \
    --output_dir data/processed/networks_motif \
    --motif_threshold 0.05 \
    --seed 42
```
*Filters GRNBoost2 edges through pySCENIC motif enrichment. Only edges with cis‑regulatory motif support (p ≤ 0.05) are retained. Produces motif‑validated network files.*

### 5. Rewiring Detection & Sensitivity Sweep
```bash
python src/network_inference/rewiring.py \
    --network_dir data/processed/networks_motif \
    --thresholds 0.01 0.05 0.1 \
    --normalize zscore \
    --output data/processed/rewiring_events.csv \
    --seed 42
```
*Generates `rewiring_events.csv` with z‑score normalized weight deltas and stability scores. Edge weights are normalized within each window before inter‑window Δ computation.*

### 6. GWAS Mapping & Enrichment Testing
```bash
python src/clinical_analysis/gwas_mapping.py \
    --gwas_source "https://www.ebi.ac.uk/gwas/" \
    --output data/processed/gwas_mapped.json

python src/clinical_analysis/enrichment.py \
    --rewiring data/processed/rewiring_events.csv \
    --gwas data/processed/gwas_mapped.json \
    --background matched \
    --iterations 5000 \
    --fdr_method bh \
    --output data/processed/disorder_enrichment.csv \
    --seed 42
```
*Applies hypergeometric test with matched-gene background (controls for gene length, expression, degree). Matched background: for each disorder, generate control gene set matched on these three attributes. Benjamini‑Hochberg FDR correction across all disorders. A sufficient number of permutations for empirical p-value. Reports vulnerability_window (developmental stage with strongest enrichment) and odds_ratio in output.*

### 7. Independent Validation
```bash
python src/clinical_analysis/validation.py \
    --rewiring data/processed/rewiring_events.csv \
    --independent_sc "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147457" \
    --bulk_brainspan "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE36520" \
    --output data/processed/disorder_enrichment.csv \
    --seed 42
```
*Adds `is_validated` flag to enrichment table. Replicates rewiring detection on independent scRNA cohort (Jaccard ≥ 0.7). Tests whether rewired hub TFs are differentially expressed in bulk BrainSpan across same developmental windows.*

### 8. Visualization & Report Generation
```bash
python src/utils/plotting.py \
    --networks data/processed/networks_motif \
    --rewiring data/processed/rewiring_events.csv \
    --enrichment data/processed/disorder_enrichment.csv \
    --output_dir results/
```
*Creates Plotly HTML network visualizations and Cytoscape-compatible JSON. Generates markdown summary report. All statements framed as associational (FR‑008).*

## Troubleshooting
- **MemoryError**: The pipeline will automatically enable `SAMPLED_MODE=True` (a subset of cells) and log the decision.  
- **LISI Failure**: Check `data/raw/metadata.csv` for donor imbalance; consider removing problematic donors.
- **Pseudotime Marker Correlation < 0.6**: Indicates residual batch effects or trajectory inference failure. Pipeline aborts with clear error; review batch-correction and marker selection.
- **Zero Permutation p‑value**: The output will show `"p < 1/5000"` per FR‑013.  
- **Motif Step Skipped**: If `pyscenic` fails to install, the pipeline continues without motif validation but logs the limitation.

---