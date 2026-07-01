# Quickstart: Predicting Molecular Interactions in Polymer Composites with Graph Neural Networks

## Prerequisites

- Python 3.11+
- 2 CPU cores, ≤7 GB RAM (GitHub Actions free tier compatible)
- Git

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-413-predicting-molecular-interactions-in-pol
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## Execution Steps

### 1. Data Pipeline (FR‑001, FR‑002, SC‑001)

```bash
python code/data/download.py   # Downloads MolNet, records checksum
python code/data/clean.py      # Validates columns, aborts with E‑DATA‑001 if adhesion_energy missing
```

*Output*: `data/curated/curated_dataset.csv`

### 2. Graph Construction (FR‑002, VII)

```bash
python code/data/graph_build.py   # Generates PyG graphs and analysis/topology_audit.md
```

*Output*: `data/processed/graphs.pt`

### 3. Model Training (FR‑003, FR‑004, SC‑002)

```bash
python code/models/train.py   # 3‑layer GAT, batch ≤32, checkpoint every 10 epochs
```

*Outputs*: `results/model.pt`, `results/performance.json`

### 4. Statistical Validation (FR‑005, FR‑006, FR‑007, FR‑008, SC‑003‑SC‑005)

```bash
# Permutation test with full re‑training on reduced subset
python code/analysis/perm_test.py   # 1000 permutations, 20 epochs each, runtime ≤2 h

# Feature attribution
python code/analysis/attribution.py   # Integrated Gradients on test samples

# Collinearity reporting
python code/analysis/collinearity.py   # VIF on handcrafted descriptors
```

*Outputs*: `results/stats.csv`, `analysis/topology_audit.md`, `analysis/power_analysis.md`

### 5. State Hashing (Principle V)

```bash
python code/utils/hash_state.py   # Updates artifact hashes in state/projects/...yaml
```

### 6. Verify Contracts

```bash
pytest tests/contract/
```

## Troubleshooting

- **E‑DATA‑001**: Adhesion energy missing. Check `logs/clean.log` for available outcome variables. The pipeline cannot continue without the target variable.
- **OOM**: Reduce `BATCH_SIZE` in `config.yaml` to 16.
- **Timeout**: If training exceeds 4.5 h, the script checkpoints and resumes automatically; total runtime limit is 6 h.
