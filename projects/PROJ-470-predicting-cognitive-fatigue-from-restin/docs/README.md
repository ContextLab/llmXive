# Predicting Cognitive Fatigue from Resting-State EEG Complexity

## Overview
This project implements a pipeline to analyze EEG data for cognitive fatigue markers using Lempel-Ziv Complexity and Permutation Entropy.

## Structure
- `code/`: Source code for the pipeline
- `data/`: Raw, processed, and analysis data
- `docs/`: Documentation

## Usage
1. Install dependencies: `pip install -r code/requirements.txt`
2. Configure `code/config.yaml`
3. Run pipeline: `python code/download.py && python code/preprocess.py && python code/features.py && python code/analysis.py && python code/report.py`

## License
MIT
