# Quickstart: Predicting the Impact of Molecular Chirality on Flavor Perception

## Prerequisites

- Python 3.11+
- Git
- 7GB+ free RAM, 14GB+ disk
- GitHub Actions free-tier runner (or local equivalent)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-202-predicting-the-impact-of-molecular-chira
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r code/requirements.txt
   ```

3. Verify dependencies:
   ```bash
   python -c "import rdkit, openmm, mdanalysis, pymc; print('All imports OK')"
   ```

## Running the Pipeline

### Step 1: Download Data & Check Fallback
```bash
python code/01_download_data.py
```
- Downloads curated chiral pairs and AlphaFold PDBs.
- Checks FlavorDB coverage; if <50%, triggers `01_fallback_chembl.py`.
- Output: `data/raw/curated_chiral_pairs.csv`, `data/raw/receptors.tar.gz`

### Step 2: Prepare Receptors & Conformers
```bash
python code/02_prepare_receptors.py
```
- Extracts PDBs, filters by pLDDT ≥70 in **pre-defined** pocket, generates 3D conformers for enantiomers.
- Output: `data/interim/conformers.sdf`, `data/interim/receptors_filtered.pdb`

### Step 3: Docking
```bash
python code/03_dock_enantiomers.py
```
- Runs AutoDock Vina (CPU-only) for all pairs.
- Output: `data/processed/docking_results.csv`

### Step 4: MD Refinement (Stability Screen)
```bash
python code/04_md_refinement.py
```
- Runs nanosecond-scale MD on top 10 complexes with OpenMM (GBSA).
- Output: `data/processed/md_trajectories/`, `data/processed/interaction_fingerprints.csv`

### Step 5: Validation Docking (FR-009)
```bash
python code/07_validation_docking.py
```
- Runs SMINA and PLANTS on top-ranked pairs.
- Output: `data/processed/validation_scores.csv`

### Step 6: Statistical Analysis
```bash
jupyter notebook code/06_statistical_analysis.ipynb
```
- Runs Wilcoxon, Spearman (with covariates), FDR, sensitivity analysis, bootstrapping, and Bayesian fallback.
- Checks success metric |ρ| > 0.3.
- Output: `data/processed/statistical_results.csv`, `data/processed/sensitivity_analysis.csv`, figures in `data/processed/plots/`

## Verification

- Check runtime: Should be ≤6 hours on GitHub Actions.
- Check memory: Peak ≤7GB during MD.
- Check outputs: All CSVs present, checksums match state YAML.
- Check sensitivity analysis: `sensitivity_analysis.csv` must exist.

## Troubleshooting

- **Docking fails**: Check ligand/receptor compatibility; log errors in `docking_errors.log`.
- **MD OOM**: Reduce simulation length or number of complexes; check `md_memory.log`.
- **Missing sensory data**: Fallback to ChEMBL set; ensure `data/raw/chembl_chiral_pairs.csv` exists.
- **Power issues**: If Wilcoxon p-value is >0.05, check Bayesian output in notebook for effect size distribution.
