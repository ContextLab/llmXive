# Quickstart: Predicting Antibiotic Resistance Evolution from Genomic Sequences

## Prerequisites
- Python 3.11+  
- Git  
- Linux environment (GitHub Actions runner or local VM) with at least 2 CPU cores and 7 GB RAM.  
- System packages for Snippy and ARIBA (install via `apt` or Docker).  

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-027-predicting-antibiotic-resistance-evoluti

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install Python dependencies
pip install -r code/requirements.txt
```

*Note*: Snippy and ARIBA are external binaries; on Debian/Ubuntu you can install them with:

```bash
sudo apt-get update
sudo apt-get install -y snippy ariba
```

Alternatively, use the provided Docker image:

```bash
docker build -t resist-pipe -f Dockerfile .
docker run --rm -v "$(pwd):/work" resist-pipe bash -c "python /work/code/main.py --stage ingest"
```

## Running the Full Pipeline

All steps are orchestrated through `code/main.py`. The `--stage` flag selects the pipeline component.

### 1️⃣ Ingestion & Phenotype Fetch (FR‑001 satisfied)
```bash
python code/main.py --stage ingest \
    --n-isolates many \
    --genbank-url https://huggingface.co/datasets/pulmo/ncbi-genbank-complete/resolve/main/data/part000/train-00000.parquet \
    --phenotype-api https://www.ncbi.nlm.nih.gov/pathogens/
```
- Downloads the GenBank parquet, filters for *E. coli* (using its taxonomic identifier), extracts FASTA files, and queries the NCBI Pathogen Detection API for AST metadata.  
- Outputs: `data/processed/feature_matrix_filtered.csv`.

### 2️⃣ Contract Validation (mandatory gate)
```bash
pytest tests/contract/
```
- Failure → pipeline aborts. Passes → continue.

### 3️⃣ Model Training (FR‑004, FR‑009)
```bash
python code/main.py --stage train \
    --target-antibiotic ceftriaxone   # repeat for each antibiotic class of interest
```
- Trains Logistic Regression (L1) and Random Forest with phylogenetically‑blocked 5‑fold CV.  
- Saves models under `data/models/` and metrics under `data/models/metrics.json`.  
- Generates auxiliary files `data/processed/feature_ranking.csv` and `data/processed/class_to_genes.json`.

### 4️⃣ Statistical Validation (FR‑005, FR‑006)
```bash
python code/main.py --stage validate \
    --target-antibiotic ceftriaxone \
    --permutations 1000
```
- Runs phylogenetically‑aware **label permutation** test (1000 iterations) and threshold sweep.  
- Outputs JSON files in `data/results/`.

### 5️⃣ Versioning (Constitution V)
```bash
python code/utils/hash_artifacts.py
```
- Computes SHA‑256 hashes for all files in `data/` and `code/`, updates `state/` metadata.

### 6️⃣ Visualization (FR‑007)
```bash
python code/main.py --stage viz --target-antibiotic ceftriaxone
```
- Generates ROC, PR, and feature‑importance plots under `data/figures/`.

### 7️⃣ Verification Summary (new verification step)
```bash
python code/04_validate/verify_results.py
```
- Consumes `data/models/metrics.json`, `data/processed/feature_ranking.csv`, and `data/processed/class_to_genes.json`.  
- Writes `data/processed/verification_summary.json` containing AUC, p‑value, top‑10 feature table, and FP/FN rates across thresholds.  
- The CI job fails if any required metric is missing or if the permutation p‑value ≥ 0.05.

## Full Test Suite

```bash
pytest tests/
```
- Runs unit, integration, and contract tests. All must pass (exit 0) before the CI job is considered successful.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `MemoryError` during Snippy | Too many isolates in memory | Reduce `--n-isolates` (e.g., 500) or increase batch size. |
| `ariba` not found | System binary missing | Install via `apt` or use the Docker image. |
| Contract test fails (`feature_matrix.schema.yaml`) | Missing required column | Re‑run ingestion with `--n-isolates` ≥ 50; ensure VIF filtering does not drop all features. |
| Permutation test exceeds time limit | `--permutations` too high | Use the default 1000; the CI runner caps at 6 h. |
| No model files after training | Target class had < 50 resistant isolates | The pipeline automatically skips that class and logs warning W001. |
| Verification step reports missing files | Earlier stage failed to generate required artifacts | Ensure steps 3 and 4 completed successfully; check `data/models/metrics.json`, `data/processed/feature_ranking.csv`, `data/processed/class_to_genes.json`. |

---



