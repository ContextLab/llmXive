# Quickstart: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## Prerequisites

- Python 3.11+
- `git`
- `conda` (optional, for `bedtools` if needed, otherwise pure Python implementation)

## Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-798-systematic-assessment-of-non-coding-vari
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

2. **Verify Dependencies**
   ```bash
   python -c "import pandas, biopython, scikit-learn; print('Dependencies OK')"
   ```

## Running the Pipeline

### Option A: Synthetic Data Mode (CI Default)
Run the full pipeline with mock data to verify logic and performance.
**Warning**: This mode validates code logic only. Biological conclusions are untestable.
```bash
python code/main.py --mode synthetic --seed 42
```
*Output*: `data/derived/filtered_snps.parquet`, `data/derived/scores.parquet`, `data/derived/enrichment_results.parquet`.

### Option B: Real Data Mode (Requires Network)
Attempts to download real data from public FTPs (1000 Genomes, JASPAR, ENCODE, GWAS Catalog). Fails gracefully to synthetic mode if network is unavailable or data is missing.
```bash
python code/main.py --mode real --seed 42
```

## Verification

1. **Check Checksums**:
   ```bash
   cat data/checksums.json
   ```
2. **Run Tests**:
   ```bash
   pytest tests/
   ```
3. **Inspect Results**:
   ```bash
   python -c "import pandas as pd; df = pd.read_parquet('data/derived/enrichment_results.parquet'); print(df.head())"
   ```

## Troubleshooting

- **OOM Error**: Reduce the `--batch-size` in `config.py`.
- **No Data Found**: Ensure `--mode synthetic` is used if FTPs are unreachable.
- **Missing JASPAR**: The script will fall back to the cached subset if download fails.