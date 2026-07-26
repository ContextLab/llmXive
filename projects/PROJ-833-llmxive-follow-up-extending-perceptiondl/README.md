# PROJ-833: llmXive Follow-up - Extending PerceptionDLM Parallel Region Perception

## Overview
This project investigates the limits of parallel region perception in large language models, specifically focusing on the "overflow hypothesis" where coherence degrades as the number of regions exceeds the model's effective context window.

## Structure
- `code/`: Python modules for data generation, model inference, and analysis.
- `data/`: Raw inputs, synthetic datasets, and processed results.
 - `raw/`: Original source data (e.g., COCO-Stuff samples).
 - `synthetic/`: Generated images with bounding boxes and annotations.
 - `processed/`: Inference results, metrics, and regression data.
- `tests/`: Unit, integration, and contract tests.
- `specs/`: Feature specifications and design documents.
- `contracts/`: JSON schemas for data validation.

## Prerequisites
- Python 3.11+
- See `requirements.txt` for dependencies.

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run the full pipeline: `python code/main.py`
3. View results in `data/processed/`.

## Design Decisions
- **Model Consistency**: We use PerceptionDLM for both parallel and sequential baselines (with context-reset) to avoid architectural confounds.
- **Memory Safety**: Runtime memory monitoring with adaptive sample reduction is enforced.
- **Statistical Rigor**: Bonferroni correction is applied to all regression significance tests.
