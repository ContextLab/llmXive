# Pipeline Implementation Guide

## Overview

This guide details the execution order and dependencies for the solubility prediction pipeline.

## Execution Phases

### Phase 1: Setup
- Initialize project structure.
- Configure linting (flake8/black).
- Set up environment variables and seeds.

### Phase 2: Data Foundation
1. **Download**: `python code/data/download_esol.py`
 - Output: `data/raw/esol.csv`
2. **Preprocess**: `python code/data/preprocess.py`
 - Input: `data/raw/esol.csv`
 - Output: `data/processed/graphs.json`
3. **Split**: `python code/data/split.py`
 - Input: `data/processed/graphs.json`
 - Output: `data/processed/splits.json`

### Phase 3: Model Training
1. **Baseline**: `python code/training/train_baseline.py`
 - Input: `data/processed/`
 - Output: `models/baseline.pkl`, `results/baseline_metrics.json`
2. **GNN**: `python code/training/train_gnn.py`
 - Input: `data/processed/`
 - Output: `models/gnn.pt`, `results/gnn_metrics.json`

### Phase 4: Analysis & Reporting
1. **Stats**: `python code/evaluation/statistical_test.py`
2. **Interpretability**: `python code/evaluation/interpretability.py`
3. **Report**: `python code/evaluation/report_generator.py`
 - Output: `results/final_report.txt`

## Troubleshooting

- **RDKit Errors**: Ensure SMILES strings are valid. The pipeline logs invalid counts.
- **Memory Issues**: If GNN training fails, reduce `hidden_dim` in `code/models/gnn_mpnn.py`.
- **Seed Consistency**: Always run `set_seed` before training to ensure reproducibility.
