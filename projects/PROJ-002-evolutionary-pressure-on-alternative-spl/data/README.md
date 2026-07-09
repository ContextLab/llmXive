# Data Directory

This directory stores all data artifacts generated or consumed by the pipeline.

## Subdirectories
- `raw/`: Original downloaded data (FASTQ files from SRA)
- `interim/`: Intermediate files (BAMs, PSI tables)
- `processed/`: Final analysis outputs (enrichment results, plots)

**Note**: Large files in `raw/` may be excluded from version control via `.gitignore`.
