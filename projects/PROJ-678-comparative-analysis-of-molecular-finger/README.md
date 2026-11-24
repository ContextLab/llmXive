# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This project compares two molecular fingerprint representations — Morgan
fingerprints (radius=2, 2048 bits) and MACCS keys (166 bits) — for
predicting toxicity endpoints in organophosphate compounds isolated from
the Tox21 dataset.

## Research Question

Do the specific P=O and P-S bond environments characteristic of
organophosphate toxicity rely on local substructure presence (captured by
MACCS keys) or extended topological context (captured by Morgan
fingerprints), and does one representation significantly outperform the
other for this chemical class?

## Pipeline Overview

1. **Download** — fetch the Tox21 dataset from HuggingFace
 (`deepchem/tox21`) into `data/raw/tox21_raw.csv`.
2. **Filter** — apply the SMARTS pattern `[P](=O)([O,SC])[O,SC]` to
 isolate organophosphates into
 `data/processed/organophosphates_filtered.csv`.
3. **Fingerprints** — generate Morgan and MACCS fingerprints with RDKit.
4. **Split** — greedy maximal dissimilarity splits (Tanimoto < 0.85):
 a single held-out test split plus K-fold (K=5) splits.
5. **Train** — Random Forest classifiers (100 trees, max_depth=15) on
 CPU only.
6. **Evaluate** — ROC-AUC / PR-AUC metrics, Corrected Resampled t-test
 (Nadeau & Bengio) on K-fold scores, bootstrap confidence intervals,
 and phosphorus-centered feature importance analysis (SC-003).

## Installation

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

All dependencies are pinned for reproducibility. Note that `numpy` is
pinned to 2.x because `datasets` requires `pyarrow`, whose binary wheels
need NumPy 2.0 or newer.

## Usage

Run the full pipeline sequentially (see `quickstart.md`):

```bash
python code/download.py
python code/filter.py
python code/fingerprints.py
python code/split.py
python code/train.py
python code/evaluate.py
```

Run the test suite:

```bash
pytest tests/
```

## Project Structure

```text
├── code/ # Pipeline scripts (download, filter, fingerprints, split, train, evaluate)
├── data/raw/ # Downloaded Tox21 data
├── data/processed/ # Filtered datasets, fingerprints, splits, models, reports
├── tests/ # Unit and integration tests
├── requirements.txt
└── pyproject.toml
```

## Constraints

- CPU-only execution (no GPU/CUDA); designed for a 2-core CI runner
 with 7 GB RAM.
- All data is real (Tox21 via HuggingFace); no synthetic data.
- Random seed 42 everywhere for reproducibility.
- Tanimoto similarity threshold of 0.85 is never relaxed for splits.

## License

For research use within the llmXive automated science pipeline.