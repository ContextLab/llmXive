# Quickstart: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## 1. Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for fetching data)
- GitHub Actions runner (2 CPU, 7GB RAM) or local equivalent.

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-798-systematic-assessment-of-non-coding-vari

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

The pipeline is executed via the `main.py` entry point.

```bash
# Run the full analysis
python code/main.py \
  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/" \
  --jaspar-url "http://jaspar.genereg.net/" \
  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/" \
  --output-dir data/output
```

### Steps Performed:
1.  **Data Ingestion**: Fetches and filters SNPs, loads PWMs, fetches GWAS leads.
2.  **Scoring**: Calculates $\Delta Score$ for all valid SNP-TF pairs.
3.  **Permutation**: Runs 100 permutations for null distribution.
4.  **Enrichment**: Performs KS tests and West-Stephens FDR correction.
5.  **Reporting**: Generates `results_summary.csv` and `report.md`.

## 4. Verification

After completion, verify the output:

```bash
# Check for significant TFs
grep "TRUE" data/output/results_summary.csv

# Verify checksums
python code/utils/checksum.py data/output/
```

## 5. Troubleshooting

- **OOM Error**: Reduce batch size in `config.py`.
- **404 Error on Data**: Ensure the canonical FTP URLs in the spec are still active. The pipeline does not use fallback URLs.
- **Slow Runtime**: Verify that permutations are capped at 100 and no GPU code is being invoked.
