# Quickstart: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Prerequisites
- Python 3.11+, `git`, internet access (HuggingFace `datasets` fetch of OQMD)  
- ~7 GB RAM, ~14 GB disk, CPU‑only (GitHub Actions free tier)

## Installation
```bash
git clone <repository-url>
cd PROJ-355-predicting-the-impact-of-impurity-cluste
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
`requirements.txt` pins: `datasets`, `pymatgen`, `ase`, `scikit-learn`, `statsmodels`, `numpy`, `pandas`, `matplotlib`, `pyyaml`, `pytest`.

## Run the Full Pipeline
```bash
python -m code.main --mode full
```
The pipeline executes the steps described in `plan.md`:

1. **Download OQMD** (verified loader, ≤3 retries). Materials Project data are omitted (waiver).  
2. **Reconstruct bulk structures** from formula + `volume_per_atom`.  
3. **Compute bulk‑lattice clustering descriptors** (RDF peak, pair‑correlation, Voronoi count) **on the bulk lattice region only**.  
4. **Build GB supercells** and insert impurities at the interface; filter zero‑impurity cases (edge‑case logging).  
5. **Generate segregation energies** with validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn (≥200 labeled configs).  
6. **Assemble training set** (`data/processed/training_set.csv`).  
7. **Linearity assessment** – Ramsey RESET test decides primary model.  
8. **Train Linear Regression** (with robust SE p‑values) **and RandomForest** under 5‑fold CV (or LOOCV if N < 5).  
9. **Power analysis** (f² = 0.15, α = 0.05, target ≥ 0.80; medium effect per Cohen, 1992).  
10. **Apply Bonferroni correction** to all coefficient tests; hypothesis report written to `results/hypothesis_report.json`.  
11. **Generate figure** `results/cluster_size_vs_segregation.png` (post‑insertion cluster‑size vs. segregation energy, for visualization only).  
12. **Write metrics** to `results/metrics.json` (validated against `contracts/output.schema.yaml`) and `results/hypothesis_report.json`.  

## Inspect Results
```bash
cat results/metrics.json
cat results/hypothesis_report.json
display results/cluster_size_vs_segregation.png   # or open with any image viewer
```

## Run Tests
```bash
pytest tests/
```
The test suite verifies:

- **`.gitignore`** contains the required four lines, as shown in the snippet below.  
- **`README.md`** includes the project title, execution instructions, and data‑provenance details; see the `README.md` snippet below.  
- End‑to‑end pipeline execution (`--mode ci`) on a reduced sample set (fits within the 6‑hour CPU limit); all artifacts are validated against the contracts.

## CI Execution
The platform runner executes `python -m code.main --mode ci` with a reduced sample size, staying within the 6‑hour CPU limit; all **generated** artifacts are validated against the contracts.

## Project `.gitignore` (example)

```text
# .gitignore
data/
results/
__pycache__/
*.pyc
```

## Project `README.md` (example)

```markdown
# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Overview
This repository implements a reproducible pipeline that links **bulk‑lattice** impurity‑clustering descriptors to segregation‑energy labels generated with validated EAM potentials. The study uses **only open OQMD data** (Materials Project data are omitted
due to lack of an unauthenticated public source).

## Quickstart
```bash
git clone <repo-url>
cd PROJ-355-predicting-the-impact-of-impurity-clustering
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m code.main --mode full
```

## Data Provenance
- **Bulk alloy records**: OQMD, loaded via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`  
  (verified URLs listed in `research.md`).  
- **Segregation energies**: generated in‑house with EAM potentials (cited in `code/extract_energy.py`).  

## Reproducibility
- All random seeds are fixed in `code/`.  
- `requirements.txt` pins exact package versions.  
- SHA‑256 checksums for raw and derived files are stored in `data/metadata.yaml`.

## License
[Specify appropriate open‑source license]
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `[DATA_UNAVAILABLE]` after 3 retries | Verify internet connectivity; the verified loader URL is `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`. |
| VIF ≥ 10 warnings | Expected for definitionally related descriptors; consult the collinearity JSON report – relationships are described, not removed. |
| Power shortfall (achieved N < required N) | Logged in `metrics.json`; increase OQMD sample size if compute budget permits. |
| Unexpectedly high R² | Remember that all relationships are **associational within the EAM model** (see Scope Limitation). |

---===
