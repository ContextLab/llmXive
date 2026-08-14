# Quickstart: Predicting Molecular Interactions in Protein-Ligand Complexes

## Prerequisites

- Python 3.11+
- Git
- Access to PDBbind (official website) and BindingDB (for validation)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-543-predicting-molecular-interactions-in-pro
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

## Data Setup

The pipeline automatically downloads the PDBbind v2020 refined set from the official source.
To manually verify the download:
```bash
python code/utils/io.py --download
```
This will place the raw tarball in `data/raw/` and generate a checksum.

## Running the Pipeline

1. **Ingest and Construct Graphs**:
   ```bash
   python code/data/ingest.py
   ```
   This step filters by resolution, adds hydrogens, detects water interactions (FR-009), and constructs graphs.

2. **Train the Model**:
   ```bash
   python code/models/train.py
   ```
   Training runs for up to 4 hours or until convergence. Logs are saved to `data/results/training.log`.

3. **Baseline Comparison**:
   ```bash
   python code/models/baseline.py
   ```
   Implements the Random Forest QSAR baseline for SC-001.

4. **Analyze and Validate Motifs**:
   ```bash
   python code/analysis/attribution.py
   python code/analysis/alignment.py
   python code/analysis/clustering.py
   python code/analysis/validation.py
   ```
   This generates the final motif report in `data/results/motifs.json`, including t-test and permutation results.

## Testing

Run the full test suite:
```bash
pytest tests/
```

Run specific contract tests:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: The pipeline is configured for N=1,000 samples. If memory issues persist, check `code/utils/config.py` for batch size settings.
- **Convergence Failure**: Check `data/results/training.log` for early stopping reasons. The model may need more epochs or a learning rate adjustment.
- **Missing Hydrogens**: The pipeline automatically infers missing hydrogens. If a complex is flagged for exclusion, check the `data/processed/excluded.txt` file.
- **Water Flagging**: If `water_flag` is not set as expected, verify the 3.5 Å distance heuristic in `code/data/preprocessing.py`.