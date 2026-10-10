# Quickstart: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Prerequisites
- Python 3.11 or newer
- Internet access (to download the OpenNeuro rs‑fMRI dataset)
- At least 7 GB RAM and 14 GB disk space (standard GitHub Actions free tier)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-331-investigating-the-influence-of-network-m

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Configuration

```bash
# Set random seed (ensured by utils)
export PYTHONHASHSEED=42
```

## Running the Full Pipeline

```bash
python code/main.py
```

The script will:

1. Download resting‑state fMRI for the specified subject list from OpenNeuro ds000228 (or abort if the download fails).  
2. Generate synthetic binary structural connectomes (`structural.npy`) using a degree‑preserving random graph model (seed = 42).  
3. Create rsFC matrices (`rsfc.npy`) and compute global efficiency.  
4. Enumerate all undirected 3‑node motifs and compute z‑scores (`motif_profile.json`).  
5. Perform multivariate regression with VIF handling, optional PCA, Bonferroni correction (α = 0.05/13), permutation testing, and a power‑analysis for N = 50, α_adj = 0.05/13, power = 0.80.  
6. Generate `results/results.pdf` containing one page per motif with a scatter plot, partial Pearson **and** Spearman coefficients, corrected p‑value, empirical‑test outcome, VIF diagnostics, and a statement of significance.  
7. Write a detailed `data/logs/pipeline.log` and `data/processed/manifest.json`.

## Inspecting Results

- **Log file**: `data/logs/pipeline.log` – look for any warnings about missing subjects or data.  
- **Manifest**: `data/processed/manifest.json` – confirms ≥ 95 % subjects processed (SC‑001).  
- **Report**: Open `results/results.pdf` in any PDF viewer. Each motif page shows the scatter plot, partial Pearson & Spearman r, raw and Bonferroni‑corrected p‑values, empirical p‑value, VIF, and significance flag. The disclaimer string is searchable.  

## Testing

```bash
pytest tests/
```

All unit, integration, and contract tests should pass.  

## Troubleshooting

- **Missing OpenNeuro data**: If the CI runner cannot download the dataset, the pipeline will abort with a clear error; no synthetic data will be fabricated beyond the structural connectome (which is always generated).  
- **Timeout on motif enumeration**: If a subject exceeds 300 s, the script aborts that subject, logs a timeout warning, and continues with remaining subjects (SC‑002).  
- **VIF ≥ 5**: The regression will automatically switch to Ridge Regression; the report will note this change.  
- **Collinearity among motifs**: If VIF indicates severe multicollinearity, the pipeline will perform PCA on the motif z‑score matrix and use the retained components in the regression.  
- **PDF too large**: The report generation step enforces a ≤ 5 MB size limit; if exceeded, the script reduces figure DPI and retries.

---


