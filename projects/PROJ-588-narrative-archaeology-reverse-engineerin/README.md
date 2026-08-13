# Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

**Project ID**: PROJ-588
**Status**: MVP Implementation (User Story 1)

## Overview
This project implements a pipeline to reverse-engineer narrative memories from fMRI data,
specifically focusing on the "Natural Stories" dataset (OpenNeuro ds000234).
The goal is to decode neural patterns associated with early vs. late event phases
and reconstruct narrative elements (plot, character, theme).

## Project Structure
```
.
├── code/ # Source code
│ ├── config.py # Global configuration, seeds, paths
│ ├── utils/ # Utility functions (stats, viz)
│ ├── data/ # Data ingestion, preprocessing, segmentation
│ └── models/ # RSA, decoding, semantic analysis
├── data/ # Data storage (raw, processed)
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
└── setup.py # Project setup (optional)
```

## Quick Start
1. **Setup Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

2. **Configuration**:
 Edit `code/config.py` to set data paths and random seeds.

3. **Run Pipeline**:
 See individual module scripts in `code/data/` for download and preprocessing.

## Dependencies
- Python 3.11+
- PyTorch (CPU only)
- Nilearn
- Transformers
- Pandas, NumPy, Scikit-learn
- OpenNeuro CLI

## License
MIT
