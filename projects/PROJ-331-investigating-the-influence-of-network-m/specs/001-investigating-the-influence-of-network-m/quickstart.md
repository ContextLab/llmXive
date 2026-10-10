# Quickstart: Investigating the Influence of Network Motifs on Resting-State Functional Connectivity

## Prerequisites
- Python 3.11+, internet access, ~7 GB RAM / ~14 GB disk

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-331-investigating-the-influence-of-network-m
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
pre-commit install   # optional, uses .pre-commit-config.yaml (flake8 + black)
```

## Run the pipeline

```bash
python code/main.py
```

Steps performed:
1. Download (stream) the verified OpenNeuro fsLR-64k parquet; select up to 50 subjects; checksum raw data.
2. Parcellate to 100 nodes; compute `rsfc.npy`, rsFC strength, global efficiency.
3. If real structural connectomes are obtainable: build binary undirected adjacency, enumerate 3- and 4-node motifs, z-scores vs. ≥1000 degree-preserving nulls. If not obtainable, the pipeline logs the gap and gates the motif–rsFC association stage (no synthetic stand-in).
4. Partial Pearson/Spearman correlations controlling global degree; Bonferroni (α = 0.05/13); ≥1000-permutation empirical p; VIF and pairwise-collinearity diagnostics; power analysis (N = 50, power = 0.80).
5. Generate `results/results.pdf` (scatter + CI per motif, all p-values, disclaimer string, power section).

## Inspect results
- `data/logs/pipeline.log` — all steps, warnings, errors, constants, library versions
- `data/processed/manifest.json` — cohort status (SC-001 check)
- `results/results.pdf` — per-motif pages; search for "These findings are associational only and do not imply causation."

## Tests

```bash
pytest tests/            # unit + integration + contract
flake8 code/ tests/      # lint (config in .flake8)
black --check code/ tests/
```

## Troubleshooting
- **Download failure**: pipeline aborts with a clear error; nothing is fabricated.
- **Structural data unavailable**: motif association stage is skipped with an explicit log entry and a limitations paragraph in the PDF; resolve by naming a verified open diffusion dataset in the spec.
- **Motif timeout (>300 s)**: subject aborted with warning; suggestion logged to reduce motif size.
- **PDF > 5 MB**: figure DPI reduced automatically and regeneration retried.
