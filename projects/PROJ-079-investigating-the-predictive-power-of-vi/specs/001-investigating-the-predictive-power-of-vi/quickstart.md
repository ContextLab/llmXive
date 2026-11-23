# Quickstart: Predictive Modeling of Host Immune Response from Viral Sequence Features

## Prerequisites

- Python 3.11+
- Git
- Internet access (for downloading datasets)
- 14 GB disk space (for raw data and artifacts)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-079-investigating-the-predictive-power-of-vi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the `main.py` script.

### Step 1: Download Data
```bash
python src/main.py --step download
```
- Downloads viral genomes from NCBI Virus and host expression data from GEO.
- Generates `data/manifest.json` with checksums.

### Step 2: Preprocess
```bash
python src/main.py --step preprocess
```
- Normalizes counts (TMM).
- Maps ISG genes (with orthologs if needed).
- Calculates ISG-PC1 scores.

### Step 3: Extract Features
```bash
python src/main.py --step features
```
- Computes CAI, GC content, k-mers (3-6), repeat density.
- Calculates protein stability (ESM-1b or Proxy).

### Step 4: Model Training
```bash
python src/main.py --step train
```
- Splits data (strain-level).
- Trains Elastic Net with 5-fold CV.
- Runs 1000-permutation test.
- Computes Debiased Lasso p-values.

### Step 5: Visualization
```bash
python src/main.py --step viz
```
- Generates feature importance plots.
- Generates partial dependence plots.

### Full Pipeline
```bash
python src/main.py --step all
```

## Output

- **Metrics**: `data/artifacts/model_metrics.json` (R², RMSE, p-values).
- **Plots**: `data/artifacts/plots/` (Feature importance, PDP).
- **Models**: `data/artifacts/model.joblib`.
- **Logs**: `logs/pipeline.log`.

## Troubleshooting

- **Runtime Exceeds 4 Hours**: The pipeline will abort. Check `logs/pipeline.log` for the bottleneck. Consider reducing the dataset size or switching to a GPU escape hatch if ESM-1b is the bottleneck.
- **Missing Genomes**: If >10% of samples lack a virus strain link, the pipeline aborts (FR-014). Verify the GEO metadata.
- **Small Dataset**: If <30 observations, the pipeline aborts (FR-013).
