# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs)`
  - script usage: `main.py [-h] [--dbsnp-ftp DBSNP_FTP] [--jaspar-url JASPAR_URL]`
  - argparse error: `main.py: error: unrecognized arguments: --encode-ftp ftp://ftp.ebi.ac.uk/pub/databases/encode/ --max-tf 200   # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs)`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs) (rc=2); python -m jsonschema -i data/output/results_summary.csv contracts/enrichment_result_schema.schema.yaml (rc=1)

## Failing / missing run-book commands

- python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs) -> rc=2

usage: main.py [-h] [--dbsnp-ftp DBSNP_FTP] [--jaspar-url JASPAR_URL]
               [--gwas-ftp GWAS_FTP] [--output-dir OUTPUT_DIR]
main.py: error: unrecognized arguments: --encode-ftp ftp://ftp.ebi.ac.uk/pub/databases/encode/ --max-tf 200   # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs)

- python -m jsonschema -i data/output/results_summary.csv contracts/enrichment_result_schema.schema.yaml -> rc=1

/home/runner/.cache/llmxive/base-env/py311-6f1866971868/jsonschema/__main__.py:4: DeprecationWarning: The jsonschema CLI is deprecated and will be removed in a future version. Please use check-jsonschema instead, which can be installed from https://pypi.org/project/check-jsonschema/
  from jsonschema.cli import main
'contracts/enrichment_result_schema.schema.yaml' does not exist.

