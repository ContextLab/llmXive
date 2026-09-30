# PROJ-083: Investigating the Relationship Between Molecular Topology and Reaction Selectivity

## Overview
This project investigates the correlation between molecular topological indices (Wiener, Balaban, Zagreb) and reaction selectivity in Electrophilic Aromatic Substitution (EAS) reactions.

## Structure
- `code/`: Source code for ingestion, descriptor calculation, and modeling
- `data/`: Raw and processed data, model artifacts
- `tests/`: Unit, integration, and performance tests
- `specs/`: Feature specifications and design documents
- `contracts/`: Data schema definitions

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Run ingestion: `python code/ingestion.py`
3. Run descriptors: `python code/descriptors.py`
4. Run modeling: `python code/modeling.py`

## Prerequisites
- Python 3.11+
- RDKit
- scikit-learn
- statsmodels
