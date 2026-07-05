# llmXive: Predicting Perovskite Stability

Automated pipeline for predicting the stability of ABX3 perovskite structures using machine learning.

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the pipeline:
 ```bash
 python code/data/download.py
 python code/data/descriptors.py
 python code/models/train.py
 ```

## Project Structure

- `code/`: Source code modules
- `data/`: Raw and processed datasets
- `results/`: Model artifacts and metrics
- `tests/`: Test suite
- `specs/`: Design documents