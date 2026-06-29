# Quickstart: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Prerequisites
- Python 3.9 installed (via `pyenv` or system Python).
- GitHub Actions runner (or local Linux environment) with ≥ 2 CPU cores and ≤ 7 GB RAM.
- **Thermal conductivity CSV**: User must supply `data/raw/thermal/thermal_conductivity.csv` with peer-reviewed experimental values and `source_reference` field (see FR‑010).

## Setup
```bash
# Clone the repository
git clone
cd perovskite-thermal-correlation

# Create a virtual environment
python -m venv.venv
source.venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Run the Full Pipeline
```bash
# Execute the orchestrator (deterministic seed = 42)
python src/main.py --seed 42
```
The orchestrator performs the following phases in order:

1. **Ingestion** – fetch structures, load thermal data, merge → `data/cleaned/merged_perovskite.csv`.
2. **Descriptor Calculation** – compute crystallographic metrics → `data/derived/descriptors.csv`.
3. **Correlation Analysis** – stratified Pearson/Spearman + multiple‑comparison correction → `results/correlation_matrix_*.csv`.
4. **Regression Modeling** – 5‑fold CV, test evaluation, feature importance → `results/regression_summary.json`.
5. **Visualization** – scatter plots with 95 % CI saved under `figures/`.

All intermediate and final artifacts are validated against the schema in `contracts/merged_perovskite.schema.yaml`. The CI workflow (`.github/workflows/ci.yml`) runs the same commands automatically and fails if any contract validation or functional test fails.

## Inspect Results
```bash
# View correlation matrices
head results/correlation_matrix_oxide.csv

# View regression summary
cat results/regression_summary.json | jq

# Open a figure (requires an image viewer)
xdg-open figures/tilting_vs_kappa.png
```

## Reproducibility Checklist
- Random seed fixed (`--seed 42`).
- `requirements.txt` pins exact library versions.
- Checksums of all raw files recorded in `data/metadata.yaml`.
- All generated files are version‑controlled via content hashes in `state/projects/...yaml`.

**Limitations Note**: Results should be interpreted with awareness of documented limitations (structural mismatch, uncontrolled confounds, sample size/power, Slack formula applicability, descriptor multicollinearity). See `research.md` for full details.

Enjoy exploring structure–property relationships in perovskites!

---