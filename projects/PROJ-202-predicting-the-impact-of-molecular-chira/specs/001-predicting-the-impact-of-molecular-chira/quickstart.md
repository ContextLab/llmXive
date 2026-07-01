# Quickstart: Predicting the Impact of Molecular Chirality on Flavor Perception

## Prerequisites

- Python 3.11+  
- Git  
- Access to a Linux environment with **2 CPU cores** and **≥ 7 GB RAM** (GitHub Actions free tier or local machine).

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-202-predicting-the-impact-of-molecular-chira
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Running the Pipeline

### 1️⃣ Download Data
```bash
python code/download.py
```
*Downloads SMILES, AlphaFold PDBs, and creates `data/manual_enantiomer_ratings.csv` (manually curated sensory ratings).*

### 2️⃣ Prepare Structures
```bash
python code/prepare.py
```
*Generates 3D conformers (RDKit) and prepares receptors (Modeller + AMBER ff14SB).*

### 3️⃣ Docking (AutoDock Vina)
```bash
python code/dock.py
```
*Runs 20 Vina jobs (5 pairs × 2 enantiomers × 2 receptors). Output: `data/processed/docking_results.csv`.*

### 3b️⃣ Robustness Scoring (SMINA & PLANTS)
```bash
python code/dock_robust.py
```
*Rescores the **top 5 enantiomeric pairs** (20 jobs) with SMINA and PLANTS. Results appended to `docking_results.csv`.*

### 4️⃣ MD Refinement (Feasibility 100 ps)
```bash
python code/md_sim.py
```
*Simulates the top 10 complexes (100 ps each) on CPU. Generates `md_summary.csv`.*

### 5️⃣ Experimental Cross‑Reference
```bash
python code/cross_ref.py
```
*Looks up BindingDB for any available Kd/Ki values; writes `experimental_comparison.csv`. If no data are found, a log entry is created and the pipeline continues.*

### 6️⃣ Statistical Analysis & Sensitivity Sweep
```bash
python code/analyze.py
```
*Performs Shapiro‑Wilk, paired t‑test/Wilcoxon, Benjamini‑Hochberg FDR, Spearman (or point‑biserial) correlation, 10 000‑iteration bootstrap, and sweeps thresholds {0.4, 0.5, 0.6} kcal/mol. Output: `statistical_analysis.csv` (one row per threshold).*

### 7️⃣ Generate Report
```bash
jupyter nbconvert --to html notebooks/report.ipynb
```
*The notebook pulls directly from the CSVs; no hand‑typed numbers.*

## Verification

```bash
pytest tests/
```
*All contract schemas are validated; the suite should pass on a fresh runner.*

## Runtime Expectations (SC‑001)

- **Total wall‑clock time**: ≈ 2.75 h (see `plan.md` for detailed budget).  
- **Peak RAM**: < 4 GB during MD.  

## Troubleshooting

- **Memory errors**: Reduce the number of receptors in `code/config.py`.  
- **Docking failures**: Check that the receptor pLDDT ≥ 70; failing receptors are automatically excluded.  
- **Missing sensory ratings**: Edit `data/manual_enantiomer_ratings.csv` to add any literature values you locate. Pairs without ratings are omitted from the correlation step.  
- **No BindingDB data**: The pipeline logs “No experimental data found” and proceeds; this is expected for many odorant‑receptor pairs.  
- **Runtime exceeds 6 h**: Verify you are using a reduced dataset (a small number of pairs, 2 receptors). The scripts will abort if more than the allowed number of jobs are detected.