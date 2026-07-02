# PROJ-079: Investigating the Predictive Power of Viral Sequence Features on Host Immune Response

## Overview
This project implements an automated science pipeline to model the host immune response based on viral genomic sequence features. It integrates data from NCBI (viral genomes) and GEO (host expression data), performs feature extraction, and trains predictive models (Elastic Net, Debiased Lasso).

## Project Structure
- `data/raw`: Raw data downloaded from external sources.
- `data/processed`: Processed and cleaned datasets.
- `data/interim`: Intermediate data files.
- `data/artifacts`: Final model outputs, metrics, and logs.
- `src`: Source code for the pipeline.
- `tests`: Unit and integration tests.
- `artifacts/models`: Serialized trained models.
- `artifacts/plots`: Generated visualizations.

## Prerequisites
- Python 3.9+
- R (required for `rpy2` and `edgeR`)
- C++ compiler (for some dependencies)

## Installation
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Set up environment variables:
 ```bash
 cp.env.example.env
 # Edit.env to add NCBI_API_KEY and GEO accessions if needed
 ```

## Usage
Run the main pipeline:
```bash
python -m src.main
```

Run tests:
```bash
pytest tests/
```

## License
MIT
