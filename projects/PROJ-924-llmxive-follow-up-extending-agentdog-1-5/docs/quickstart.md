# Quickstart Guide: llmXive Drift Detection

This guide provides a step-by-step walkthrough for setting up and running the zero-shot drift detection pipeline.

## Prerequisites

- Python 3.11 or higher
- pip package manager
- At least 7GB of available RAM
- CPU (GPU not required, but supported for acceleration if configured)

## Installation

1. **Clone the repository** (or navigate to the project root):
 ```bash
 cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

The project uses `code/config.py` to manage paths, random seeds, and batch sizes.

Default configuration:
- **Taxonomy Model**: `all-MiniLM-L6-v2`
- **Batch Size**: 32
- **Max Memory**: 7GB
- **Drift Threshold**: 1.5

You can override these settings by modifying `code/config.py` or setting environment variables.

## Running the Pipeline

### Option 1: Full Pipeline

Run the entire drift detection workflow (Data Loading → Taxonomy Building → Scoring → Validation):

```bash
python code/run_full_pipeline.py
```

This will:
1. Fetch raw data (AdvBench, HF4, OWASP Taxonomy).
2. Build taxonomy centroids.
3. Compute drift scores for all logs.
4. Generate stratified batches for annotation.
5. (Optional) Run baseline comparison.

### Option 2: Individual Stages

You can run specific stages independently:

**1. Data Loading & Taxonomy Mapping**:
```bash
python code/data_loader.py
```

**2. Taxonomy Centroid Generation**:
```bash
python code/taxonomy_builder.py
```

**3. Drift Scoring**:
```bash
python code/drift_scoring.py
```

**4. Validation & Statistics**:
```bash
python code/validation.py
```

## Output Artifacts

After a successful run, you will find the following outputs in the `data/` directory:

- `data/raw/taxonomy_owasp.json`: Downloaded OWASP taxonomy.
- `data/processed/taxonomy_centroids.json`: Taxonomy with computed embeddings.
- `data/processed/drift_scores.csv`: Drift scores for all processed logs.
- `data/processed/blinded_annotation_batches/`: CSVs ready for human review.
- `data/processed/validation_stats.json`: Statistical validation results.

## Verification

To verify the installation and project structure:

```bash
python code/verify_project_structure.py
```

## Troubleshooting

- **Memory Errors**: Ensure your system has at least 7GB of free RAM. Reduce `batch_size` in `config.py` if needed.
- **Dataset Fetch Failures**: Ensure you have an active internet connection and that the Hugging Face datasets library is up to date.
- **Import Errors**: Make sure you are running the script from the project root and that the virtual environment is activated.

## Next Steps

- Review `data-model.md` for schema details.
- Check `specs/001-llmxive-drift-detection/` for design documents.
- Run `pytest tests/` to execute the test suite.
