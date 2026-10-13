# Quickstart: Gene Expression Dynamics Pipeline

## Prerequisites
- Python 3.11
- `pip install -r requirements.txt` (includes `GEOparse`, `scanpy`, `arboreto`, `harmonypy`)

## Execution Workflow

### 1. Data Acquisition & Integration
Run the preprocessing pipeline to fetch the human fetal brain scRNA-seq atlas and remove batch effects.
```bash
python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad
```
*Verifies: LISI score $\ge 1.2$ and $\ge 80\%$ cell retention.*

### 2. Network Inference
Infer the dynamic GRNs and identify rewiring events.
```bash
python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5
```
*Produces: Stage-specific JSON networks and `rewiring_events.csv`.*

### 3. Clinical Correlation
Map risk genes and run permutation tests.
```bash
python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json
```
*Produces: `disorder_enrichment.csv` with FDR-corrected p-values.*

### 4. Validation & Visualization
Validate findings against an independent scRNA-seq cohort and bulk RNA-seq (BrainSpan) expression data.
```bash
python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv
```

## Troubleshooting
- **Memory Errors**: If the process crashes on the CI runner, the pipeline automatically switches to a global sampled mode (a predefined number of cells). Check logs for `SAMPLED_MODE=True`.
- **LISI Failure**: If the pipeline aborts due to LISI $< 1.2$, check the `donor_id` distribution in the raw metadata.
