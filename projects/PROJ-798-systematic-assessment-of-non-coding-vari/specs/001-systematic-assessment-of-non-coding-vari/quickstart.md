# Quickstart: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

## Prerequisites
- Python 3 (recent version)  
- `git` (for cloning)  
- Internet access (to download dbSNP, ENCODE, JASPAR, GWAS files)  
- GitHub Actions runner or equivalent Linux environment (Multiple CPUs, 7 GB RAM)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-798-systematic-assessment-of-non-coding-vari

# Set up a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline
```bash
python code/main.py \
  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/" \
  --jaspar-url "http://jaspar.genereg.net/" \
  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/" \
  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/" \
  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs)
  --max-snps 500000 \          # optional sub‑sample to a limited number of SNPs for runtime safety
  --permutations 500 \         # West‑Stephens max‑T permutation count with stratified shuffling
  --output-dir data/output
```

The command performs, in order:
1. **Data ingestion** (download, checksum, LD pruning, regulatory filtering, stratification assignment, GC‑matched control generation).  
2. **Affinity scoring** (PWM loading, dynamic‑window Δ Score calculation).  
3. **Permutation & enrichment** (Multiple stratified label shuffles within LD blocks and strata, KS test with block‑aware stratified permutation, tail‑enrichment test, West‑Stephens max‑T FDR).  
4. **Reporting** (`results_summary.csv`, `report.md`).

## Verification
```bash
# Verify that the .gitignore behaves as expected
git check-ignore -v data/raw/snps_raw.vcf.gz   # should exit successfully
git check-ignore -v data/raw/source_log.txt   # should exit 1

# Validate the final results against the contract schema
python -m jsonschema -i data/output/results_summary.csv contracts/enrichment_result_schema.schema.yaml
```

## Troubleshooting
- **Out‑of‑Memory**: Reduce `--max-snps` or increase `--batch-size` in `code/config.py`.  
- **FTP 404**: Ensure the URLs are still active; the pipeline will abort with a clear message instead of fabricating data.  
- **Runtime > 6 h**: Profile with `cProfile` and consider lowering the number of TFs (`--max-tf`) or SNPs (`--max-snps`).  

---