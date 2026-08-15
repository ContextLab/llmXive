# Evolutionary Pressure on Alternative Splicing in Primates

## Project Overview
This project investigates evolutionary pressure on alternative splicing events across primates (Human, Chimp, Macaque, Marmoset) using RNA-seq data, phylogenetic conservation scores, and statistical modeling.

## Project Structure
```
.
├── code/ # Source code
│ ├── data_models/ # Data class definitions
│ ├── pipeline/ # Pipeline execution scripts
│ ├── utils/ # Utilities (logging, hashing)
│ └── setup_python_env.py
├── config/ # Configuration files (genomes, params)
├── data/ # Data directory (raw, processed)
│ ├── raw/ # Downloaded FASTQs, BAMs
│ ├── processed/ # PSI tables, annotations
│ └── figures/ # Output plots
├── specs/ # Feature specifications
├── tests/ # Test suites
├── requirements.txt # Python dependencies
├── pyproject.toml # Project config & formatting
└── README.md
```

## Prerequisites
- Python 3.11+
- R 4.3+
- External Tools: STAR, SUPPA2, bedtools, UCSC utilities

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python3.11 -m venv.venv
 source.venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```
4. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Configuration
Genome assemblies are defined in `config/genomes.yaml`. Ensure paths to reference genomes (FASTA, GTF, BigWig) are correctly set before running the pipeline.

## Running the Pipeline
See individual scripts in `code/pipeline/` for entry points.
Example:
```bash
python code/setup_python_env.py
python code/pipeline/download.py --config config/genomes.yaml
```

## License
MIT License
