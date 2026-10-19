# Quickstart: Gene Expression Dynamics Pipeline

## Prerequisites
```bash
# Python 3.11
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # includes scanpy, harmonypy, arboreto, scvelo, pyscenic, pandas, pyyaml, pytest, datasets, requests
```

## Execution Workflow

### 0. Project Initialization
```bash
python src/data_pipeline/setup_data.py \
    --seed 42 \
    --output_dir data/raw
```
*Creates `data/raw/`, streams the BICCN Human MTG dataset to produce a stratified sample, downloads GEO GSE123456 and BrainSpan metadata, and writes a checksum manifest.*

### 1. Data Acquisition & Integration
```bash
python src/data_pipeline/preprocess.py \
    --dataset human_mtg \
    --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA" \
    --output data/processed/integrated_atlas.h5ad \
    --seed 42
```
*Performs QC, normalization, Harmony batch correction, LISI assessment, and writes the integrated AnnData object. Marker‑gene validation is performed when the requested markers are present.*