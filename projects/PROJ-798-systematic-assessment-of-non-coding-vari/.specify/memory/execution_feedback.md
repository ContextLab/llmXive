# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs) (rc=1); python -m jsonschema -i data/output/results_summary.csv contracts/enrichment_result_schema.schema.yaml (rc=1)

## Failing / missing run-book commands

- python code/main.py  --dbsnp-ftp "ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/"  --jaspar-url "http://jaspar.genereg.net/"  --encode-ftp "ftp://ftp.ebi.ac.uk/pub/databases/encode/"  --gwas-ftp "ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/"  --max-tf 200 \               # limit to the most informative PWMs (i.e., a limited subset of top-ranked PWMs) -> rc=1
-798-systematic-assessment-of-non-coding-vari/code/main.py", line 57, in main
    fetch_dbsnp_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/data_ingestion/fetch_dbsnp.py", line 136, in main
    listing = list_ftp_directory(FTP_BASE)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-798-systematic-assessment-of-non-coding-vari/code/data_ingestion/data_ingestion.py", line 54, in list_ftp_directory
    ftp.cwd(path)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 625, in cwd
    return self.voidcmd(cmd)
           ^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 286, in voidcmd
    return self.voidresp()
           ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 259, in voidresp
    resp = self.getresp()
           ^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/ftplib.py", line 254, in getresp
    raise error_perm(resp)
ftplib.error_perm: 550 /snp/organisms/human_9606_b155_GRCh38p13/VCF: No such file or directory

- python -m jsonschema -i data/output/results_summary.csv contracts/enrichment_result_schema.schema.yaml -> rc=1

/home/runner/.cache/llmxive/base-env/py311-6f1866971868/jsonschema/__main__.py:4: DeprecationWarning: The jsonschema CLI is deprecated and will be removed in a future version. Please use check-jsonschema instead, which can be installed from https://pypi.org/project/check-jsonschema/
  from jsonschema.cli import main
'contracts/enrichment_result_schema.schema.yaml' does not exist.

