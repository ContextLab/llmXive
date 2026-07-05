# Brain Network Efficiency and Fluid Intelligence

## Project Overview
This project investigates the relationship between brain network efficiency (specifically global and frontoparietal efficiency) and fluid intelligence scores using data from the Human Connectome Project (HCP).

## Quickstart

### Prerequisites
- Python 3.11+
- pip

### Setup
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 python code/install_deps.py
 ```
 Or manually:
 ```bash
 pip install -r requirements.txt
 ```

### Running the Pipeline
Once dependencies are installed and data is available (see Data section), run the main orchestrator:
```bash
python code/main.py
```

### Data
- Raw data is expected in `data/raw/`
- Processed data will be saved to `data/processed/`
- Results will be saved to `data/results/`

Note: HCP data access requires registration and approval. Follow the HCP data use agreement.

## Structure
- `code/`: Source code for the pipeline
- `data/`: Data storage (raw, processed, results)
- `tests/`: Unit and integration tests
- `docs/`: Documentation
- `state/`: Project state and configuration

## License
[Insert License]
