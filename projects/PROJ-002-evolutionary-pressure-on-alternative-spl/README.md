# PROJ-002: Evolutionary Pressure on Alternative Splicing in Primates

## Overview
This project investigates lineage-specific splicing events (LSEs) across primates
(Human, Chimp, Macaque, Marmoset) and tests for enrichment in accelerated regulatory regions.

## Prerequisites
- Python 3.11+
- R 4.3+
- STAR aligner (system install)
- SUPPA2 (system install or via conda)
- UCSC bedtools (system install)

## Project Structure
```
.
├── config/ # Configuration files (genomes.yaml, etc.)
├── data/
│ ├── raw/ # Raw FASTQ/BAM files (git-ignored)
│ ├── interim/ # Intermediate processing results
│ └── processed/ # Final analysis tables
├── code/
│ ├── pipeline/ # Core pipeline scripts
│ └── utils/ # Utility modules
├── tests/ # Test suites
├── figures/ # Generated plots
├── requirements.txt # Python dependencies
├── requirements_r.txt # R dependencies
└── README.md
```

## Quick Start
1. Install Python dependencies:
 `pip install -r requirements.txt`
2. Install R dependencies (via Rscript):
 `Rscript -e "install.packages(c('phylolm', 'ape', 'data.table', 'ggplot2'))"`
3. Configure genome assemblies in `config/genomes.yaml`.
4. Run the pipeline:
 `python code/pipeline/main.py`

## License
MIT
