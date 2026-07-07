# Quickstart: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Prerequisites

- Python 3.11+
- Git
- 7GB RAM, 14GB disk (for CI runner)

## Setup

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-078-predicting-polymer-degradation-pathways-/
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

3. **Download Data**:
   ```bash
   python code/ingest.py --source nist --output data/raw/nist_polyesters.csv
   python code/ingest.py --source smiles --output data/raw/smiles_dataset.csv
   ```

## Run Pipeline

1. **Preprocess**:
   ```bash
   python code/preprocess.py --input data/raw/nist_polyesters.csv --output data/processed/graph_dataset.pt
   ```

2. **Augment** (optional, if dataset <150):
   ```bash
   python code/preprocess.py --augment --input data/processed/graph_dataset.pt --output data/processed/augmented_graph_dataset.pt
   ```

3. **Train**:
   ```bash
   python code/train.py --data data/processed/augmented_graph_dataset.pt --epochs 50 --cv 5
   ```

4. **Evaluate**:
   ```bash
   python code/evaluate.py --model models/gnn_model.pt --data data/processed/graph_dataset.pt --output reports/motif_report.yaml
   ```

## Validate Results

- Check `reports/motif_report.yaml` for:
  - Macro-F1 score (SC-001).
  - Permutation test p-values (SC-002) - both global and local.
  - Top 3-5 motifs (FR-007).
- Verify runtime <6h and memory <7GB (SC-003).

## Troubleshooting

- **Invalid SMILES**: Check logs for skipped records; ensure `rdkit` is installed.
- **Memory Error**: Reduce hidden dimension or batch size in `train.py`.
- **Missing Labels**: Check `data/processed/polymer_graphs.csv` for `flags` indicating missing pathway labels. If <50 labels, the system will attempt manual curation or shift to unsupervised mode.