# Data Directory

This directory contains raw and processed datasets for the experiment.

## Structure
- `raw/`: Original downloaded datasets (e.g., AIME 2024)
- `processed/`: Preprocessed and split datasets ready for training
- `results/`: Experiment outputs, metrics, and statistical reports

## Data Sources
- AIME 2024: `HuggingFaceH4/aime_2024` from HuggingFace Hub
- Teacher Models: Pre-trained Transformers from HuggingFace
- Student Models: MoE (SmolLM proxy) and SSM (Mamba) models

## Constraints
- All datasets must be real, no synthetic fallbacks
- Memory footprint must respect 7GB RAM limit
- Human-verified labels required for evaluation
