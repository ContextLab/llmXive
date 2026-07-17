# PROJ-976: llmXive Follow-up: Extending Trust-Region Behavior Blending for On-Policy Distillation

## Overview
This project extends the "Trust-Region Behavior Blending" (TRB) methodology by introducing **Diversity Profiles** to predict model collapse and stability without ground-truth sweep logs.
We utilize proxy targets (BEIR relevance scores, Book Corpus text length) to validate static diversity metrics.

## User Stories
- **US1**: Static Diversity Profile Computation (MVP)
- **US2**: Proxy Correlation Analysis
- **US3**: Generalization Validation

## Project Structure
- `code/`: Source implementation (metrics, pipelines, utils)
- `data/`: Raw, processed, and results data
- `specs/`: Feature specifications and contracts
- `tests/`: Unit and integration tests
- `state/`: Runtime state and artifact hashes

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

## Execution
Run the feature extraction pipeline:
```bash
python code/pipelines/extract_features.py
```
