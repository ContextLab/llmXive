# Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

## Project Overview

This project implements a **Structure-Only Surrogate Model** to predict the elastic moduli of 2D materials.

**Important Clarification**: This work does *not* perform first-principles calculations (solving the Schrödinger equation). Instead, it trains a Graph Neural Network (GNN) to interpolate elastic properties from existing Density Functional Theory (DFT) data found in public repositories (Materials Project, AFLOW). The model is a data-driven surrogate that maps structural descriptors to elastic tensors.

## Structure

- `code/`: Source code for data ingestion, model training, and analysis
- `data/`: Processed datasets and results
- `specs/`: Feature specifications and user stories
- `tests/`: Unit and integration tests

## Quick Start

1. Install dependencies: `pip install -r code/requirements.txt`
2. Run the data pipeline: `python code/ingest/pipeline.py`
3. Train the model: `python code/model/train.py`
4. Run analysis: `python code/analysis/report_generator.py`

## License

MIT License
