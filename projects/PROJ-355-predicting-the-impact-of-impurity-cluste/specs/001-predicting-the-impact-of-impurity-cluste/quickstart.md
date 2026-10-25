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

1. **Download OQMD** (verified loader, ≤3 retries). Materials Project data are omitted (waiver) due to lack of an unauthenticated open source.  
2. **Reconstruct bulk structures** from formula + `volume_per_atom`.  
3. **Compute bulk‑pre‑insertion clustering descriptors** (RDF peak, pair‑correlation, Voronoi count) **within the GB interface region *before* impurity insertion**.  
4. **Build GB supercells** and insert impurities at the interface; filter zero‑impurity cases (edge‑case logging).  
5. **Generate segregation energies** with validated EAM potentials for Fe‑Cr, Ni‑Al, Cu‑Zn (≥200 labeled configs).  
6. **Run EAM‑vs‑DFT validation** – reports `[DATA_UNAVAILABLE]` if no DFT benchmark is found; this limitation is formally **waived** (see FR‑011).  
7. **Assemble training set** (`data/processed/training_set.csv`).  
8. **Linearity assessment** – Ramsey RESET test decides primary model.  
9. **Train Linear Regression** (with robust SE p‑values) **and RandomForest** under 5‑fold CV (or LOOCV if N < 5).  
10. **Power analysis** (f² = 0.15, α = 0.05, target ≥ 0.80; medium effect per Cohen, 1992).  
11. **Apply Bonferroni correction** to all coefficient tests; hypothesis report written to `results/hypothesis_report.json`.  
12. **Generate figure** `results/cluster_size_vs_segregation.png` (post‑insertion cluster‑size vs. segregation energy, for visualization only).  
13. **Write metrics** to `results/metrics.json` (validated against `contracts/output.schema.yaml`) and `results/hypothesis_report.json`.  

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
This repository implements a reproducible pipeline that links **pre‑insertion** impurity‑clustering descriptors
computed **within the grain‑boundary interface region** to segregation‑energy labels generated with validated
EAM potentials. The study uses **only open OQMD data** (Materials Project data are omitted
due to lack of an unauthenticated public source).

## Quickstart
```bash
git clone <repo-url>
cd PROJ-355-predicting-the-impact-of-impurity-cluste
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m code.main --mode full
```

## Data Provenance
- **Bulk alloy records**: OQMD, loaded via `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`  
  (verified URLs listed in `research.md`).  
- **Segregation energies**: generated in‑house with EAM potentials (cited in `code/simulate_energy.py`).  
- **DFT benchmark**: not available from an open source; the validation harness records `[DATA_UNAVAILABLE]`.

## Reproducibility
- All random seeds are fixed in `code/`.  
- `requirements.txt` pins exact package versions.  
- SHA‑256 checksums for raw and derived files are stored in `data/metadata.yaml`.

## License
[Specify appropriate open-source license]
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `[DATA_UNAVAILABLE]` after 3 retries | Verify internet connectivity; the verified loader URL is `datasets.load_dataset("jablonkagroup/oqmd", name="raw_data")`. |
| VIF ≥ 10 warnings | Expected for definitionally related descriptors; consult the collinearity JSON report – relationships are described, not removed. |
| Validation reports `DATA_UNAVAILABLE` | No open DFT benchmark is publicly accessible; this is a documented limitation, not an error. |
| Power shortfall (achieved N < required N) | Logged in `metrics.json`; increase OQMD sample size if compute budget permits. |
| Results appear overly optimistic | Remember that all relationships are **associational within the EAM model** (see Scope Limitation). |

---===