# Quickstart: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Prerequisites

- Python 3.11+
- 2 CPU cores, 7 GB RAM, 14 GB disk (GitHub Actions free-tier)
- Internet access for dataset download (no credentials required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-078-predicting-polymer-degradation-pathways-/
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Data Setup

1. **Download verified datasets**:
 ```bash
 python code/ingest.py --source verified_smiles
 ```
 This will:
 - Fetch SMILES from HuggingFace (verified sources).
 - Filter for polyesters (ester bond detection).
 - Apply synthetic labels or flag for curation.
 - Save to `data/raw/` and `data/processed/`.

2. **Verify data integrity**:
 ```bash
 python code/utils.py --check-data
 ```
 This will:
 - Validate SMILES strings.
 - Check for missing environmental conditions.
 - Log imputation actions.

## Model Training

1. **Run augmentation** (if dataset <150 instances):
 ```bash
 python code/augment.py --expand 2x
 ```
 This will:
 - Apply edge dropout and subgraph sampling.
 - Expand dataset by 2x.
 - Save to `data/augmented/`.

2. **Train GNN**:
 ```bash
 python code/train.py --cv 5 --epochs 100
 ```
 This will:
 - Perform 5-fold cross-validation (or LOO if n<150).
 - Train lightweight GNN (≤3 layers, hidden dim ≤128).
 - Save model checkpoint to `code/models/`.

3. **Monitor training**:
 - Check `code/logs/training.log` for loss convergence.
 - Verify macro-F1 score and epoch convergence.

## Feature Attribution & Validation

1. **Compute feature importance**:
 ```bash
 python code/attribution.py --method integrated_gradients
 ```
 This will:
 - Generate `MotifImportance` scores.
 - Identify top structural motifs.

2. **Run statistical validation**:
 ```bash
 python code/validate.py --chi2-iterations 1000
 ```
 This will:
 - Perform χ² test with 1000+ iterations.
 - Generate final report with p-values and motif rankings.

3. **View report**:
 ```bash
 cat docs/reports/final_report.md
 ```

## Testing

1. **Run unit tests**:
 ```bash
 pytest tests/unit/
 ```

2. **Run integration tests**:
 ```bash
 pytest tests/integration/
 ```

3. **Run contract tests**:
 ```bash
 pytest tests/contract/
 ```

## Troubleshooting

- **API rate limits**: The system implements exponential backoff (3 retries) per FR-009.
- **Invalid SMILES**: Skipped with logging; continue processing.
- **Small dataset**: Power analysis warning triggered if n<150; LOO validation used.
- **Memory issues**: Dataset subsampled if >7GB RAM usage.
