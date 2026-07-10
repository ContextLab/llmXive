# PROJ-410: Predicting Plant Root System Architecture from Genomic Data

## Overview
This project implements a pipeline to predict plant root system architecture
using genomic data from the 1001 Genomes Project and phenotypic data from ATRDB.

## Setup

### Prerequisites
- Python 3.9+
- pip

### Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage
See individual module documentation for specific usage instructions.

### Data Pipeline
```bash
python code/download.py
python code/preprocess.py
```

### Model Training
```bash
python code/train.py
```

### Evaluation
```bash
python code/evaluate.py
python code/visualize.py
```

## Project Structure
- `code/`: Source code modules
- `data/`: Data storage (raw and processed)
- `tests/`: Test suite
- `contracts/`: Data schemas and contracts
- `figures/`: Generated visualizations

## License
MIT License