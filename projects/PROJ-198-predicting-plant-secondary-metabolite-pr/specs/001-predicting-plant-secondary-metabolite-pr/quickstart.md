# Quickstart: Predicting Plant Secondary Metabolite Profiles from Genomic Data

## Prerequisites

- Python 3.11+
- Git
- Access to NCBI RefSeq and MetaboLights (no API key required for public data, but rate limits apply).
- **Note**: antiSMASH 7.0 is a dependency. If you have Docker, the pipeline will attempt to run antiSMASH in a container. Otherwise, it will use a local installation. **Genomes > 500MB will be skipped automatically.**

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-198-predicting-plant-secondary-metabolite-pr
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **(Optional) Install antiSMASH**:
    If you have Docker installed, no action is needed. If you prefer to install antiSMASH locally:
    ```bash
    # Follow instructions at https://docs.antismash.secondarymetabolites.org/
    # Ensure 'antismash' is in your PATH.
    ```

## Running the Pipeline

### 1. Configuration
Edit `code/config.py` or `config/species_list.yaml` to define the list of plant species to analyze.
```yaml
species:
  - "Arabidopsis thaliana"
  - "Oryza sativa"
  - "Solanum lycopersicum"
  # ... add more
```

### 2. Data Download and Processing
Run the data pipeline to download genomes, predict BGCs, and align data.
```bash
python code/cli/main.py --step download_and_align
```
*This step may take 30-60 minutes depending on the number of species and antiSMASH execution time. Genomes > 500MB are skipped.*

### 3. Model Training and Evaluation
Train the models and run the sensitivity analysis.
```bash
python code/cli/main.py --step train_and_evaluate
```
*This step runs LOO cross-validation, PGLS, and the phylogenetic permutation baseline. It includes PCA dimensionality reduction.*

### 4. View Results
Results are saved to `data/processed/`.
- `aligned_matrix.csv`: The input data.
- `model_metrics.json`: Performance metrics.
- `sensitivity_analysis.csv`: Robustness check results (threshold sweep).

## Testing

Run the unit and integration tests:
```bash
pytest tests/
```

To test the pipeline on a small subset (5 species) to verify the 30-minute constraint:
```bash
python code/cli/main.py --step download_and_align --limit 5
```

## Troubleshooting

- **antiSMASH Timeout**: If the pipeline hangs for a specific species, that species will be excluded. Check logs for "Species skipped due to timeout".
- **Missing Data**: If a species has no metabolite data, it will be excluded. Check `data/interim/alignment_warnings.log` for details.
- **Memory Error**: If you encounter OOM errors, reduce the number of species in the config or increase the swap space on your machine.
- **Small Sample Size**: If N < 20, the pipeline will use LOO cross-validation instead of 5-fold.