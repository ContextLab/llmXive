# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --output-dir data/output; python code/utils/checksum.py data/output/; 1 declared deliverable(s) absent: data/raw/snps_raw.parquet

## Failing / missing run-book commands

- python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --output-dir data/output -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/main.py': [Errno 2] No such file or directory

- python code/utils/checksum.py data/output/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/utils/checksum.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/raw/snps_raw.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/snps_raw.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data_ingestion/fetch_dbsnp.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/snps_raw.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
