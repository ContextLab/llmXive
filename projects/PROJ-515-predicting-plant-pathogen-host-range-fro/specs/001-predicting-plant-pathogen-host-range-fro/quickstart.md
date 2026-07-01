# Quickstart: Predicting Plant Pathogen Host Range from Publicly Available Genomic and Interaction Data

## Prerequisites

- **Python**: 3.11 or higher.
- **System Dependencies**: `hmmsearch` (HMMER suite), `antiSMASH 7.0` (command-line version), `EffectorP 3.0` (HMM library).
- **Internet Access**: Required to download genomes (NCBI GenBank) and interaction data (PHI-Base, Interactome3D, NCBI BioSample).
- **Hardware**: CPU-only; 4 GB RAM minimum; 10 GB disk space.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd llmXive/projects/PROJ-515-predicting-plant-pathogen-host-range-fro
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Install external tools**:
 - **HMMER**: Follow instructions at Network is unreachable"))].
 - **antiSMASH 7.0**: Follow instructions at https://antismash.secondarymetabolites.org/download/.
 - **EffectorP 3.0**: Download HMM library from https://effectorp.csiro.au/.

## Running the Pipeline

### Step 1: Prepare Input Data

Create a directory `data/raw/` and populate it with:
- **Genome Files**: FASTA files for 50 pathogens (e.g., `pathogen_1.fasta`, `pathogen_2.fasta`).
- **Interaction CSV**: A file `interactions.csv` with columns: `pathogen_id`, `host_id`, `infects`, `source`.

Example `interactions.csv`:
```csv
pathogen_id,host_id,infects,source
GCF_000001234.5,Solanum lycopersicum,1,PHI-Base
GCF_000001234.5,Zea mays,0,Interactome3D
GCF_000005678.9,Solanum lycopersicum,1,NCBI BioSample
```

### Step 2: Run the Full Pipeline

Execute the pipeline with:
```bash
bash code/cli/run_pipeline.sh --data-dir./data/raw --seed 42
```

**Arguments**:
- `--data-dir`: Path to input data directory (default: `./data/raw`).
- `--seed`: Random seed for reproducibility (default: 42).
- `--mode`: Optional; `train` (default), `predict`, or `sensitivity` (for FR-016).

**Output Artifacts**:
- `results/model.pkl`: Trained logistic regression model.
- `results/feature_importance.csv`: SHAP values for all features.
- `results/significant_features.tsv`: Statistically significant feature categories.
- `logs/pipeline.log`: Processing log with timestamps.

### Step 3: Predict Host Range for a Novel Pathogen

For a new pathogen genome:
```bash
bash code/cli/predict_host_range.sh --genome./data/raw/novel_pathogen.fasta --model./results/model.pkl
```

**Output**:
- `prediction.csv`: Probability scores for each plant species in the reference interaction matrix.

Example `prediction.csv`:
```csv
host_species,prediction_probability
Solanum lycopersicum,0.85
Zea mays,0.12
Triticum aestivum,0.03
...
```

## Validation

1. **Check Model Output**:
 ```bash
 python -c "import joblib; model = joblib.load('results/model.pkl'); print(model.score(X_test, y_test))"
 ```

2. **Verify Feature Importance**:
 Ensure `feature_importance.csv` contains at least three feature categories with non-zero SHAP values (US-1, Acceptance Scenario 2).

3. **Test Sensitivity Analysis**:
 Run with `--mode sensitivity` to compare 'unknown' vs. 'negative' treatments (FR-016).

## Troubleshooting

- **Missing Genomes**: If a pathogen lacks a genome file, the pipeline logs a warning and skips it.
- **No Interactions**: If a pathogen has no interaction records across all sources, the pipeline halts with a critical error (FR-011).
- **Memory Overflow**: If memory exceeds 4 GB, reduce k-mer complexity or process pathogens in batches.
- **Runtime Exceedance**: If runtime approaches 5 hours, log warnings and prioritize critical steps.

## Next Steps

- **Customize Features**: Modify `code/features/extract_genomic_features.py` to add new genomic features.
- **Extend Databases**: Add new interaction sources by updating `code/download/fetch_interactions.py`.
- **Improve Model**: Experiment with different regularization strengths or feature selection methods.
