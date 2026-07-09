# PROJ-002: Evolutionary Pressure on Alternative Splicing in Primates

## Setup Instructions

### Prerequisites
- Python 3.11+
- R 4.3+
- System dependencies for R packages (compiler, headers)

### Python Environment Setup
1. Create a virtual environment:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 ```
2. Install Python dependencies:
 ```bash
 pip install -r requirements.txt
 ```

### R Environment Setup
1. Install R 4.3+ if not already installed.
2. Run the R dependency installation script:
 ```bash
 chmod +x install_r_dependencies.sh
./install_r_dependencies.sh
 ```

### Verification
Run the following to verify installations:
```bash
python -c "import pandas, numpy, yaml, Bio, requests, tqdm, pybedtools, pyBigWig, sklearn, loguru; print('Python OK')"
Rscript -e "library(phylolm); library(ape); library(data.table); library(ggplot2); cat('R OK\n')"
```

## Project Structure
- `src/`: Source code for pipeline modules
- `data/`: Generated data artifacts
- `tests/`: Test suites
- `config/`: Configuration files
- `docs/`: Documentation

## Running the Pipeline
See `quickstart.md` for execution instructions.
