# PROJ-833: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

## Overview
This project investigates the overflow hypothesis in PerceptionDLM by comparing
parallel vs. sequential region perception coherence as region counts increase.

## Structure
- `code/`: Source code for data generation, model inference, and analysis.
- `data/`: Raw, synthetic, and processed data.
- `tests/`: Unit and integration tests.
- `specs/`: Feature specifications and design docs.
- `docs/`: Documentation.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the pipeline: `python code/main.py`

## Key Design Decisions
- **Model Consistency**: Uses PerceptionDLM for both parallel and sequential baselines
 to isolate context-window effects from architectural differences.
- **Data Generation**: Synthetic data is generated with non-overlapping bounding boxes
 derived from real COCO-Stuff/ParaDLC-Bench samples.
- **Statistical Rigor**: Includes Bonferroni correction for regression analysis.
