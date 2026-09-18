# Quickstart: MD Diffusion Coefficient Pipeline

## Prerequisites
- Python 3.11+
- pip

## Setup
1. Install dependencies:
 ```bash
 cd code
 pip install -r requirements.txt
 ```

2. Initialize data files (NIST references):
 ```bash
 python data/raw/generate_nist_refs.py
 ```
 This creates `data/raw/nist_refs.json` and `data/raw/manifest.json`.

3. Generate topologies:
 ```bash
 python simulation/topology.py
 ```

## Execution

Run a single solvent analysis:
```bash
python main.py --solvent water --timescale 1.0
```

Run the full batch (all solvents, all timescales):
```bash
python main.py --full-batch
```

Run sensitivity analysis:
```bash
python main.py --sensitivity --solvent ethanol --timescale 10.0
```

## Outputs
- `data/processed/`: Analysis results (JSON/CSV)
- `figures/`: Generated plots (PNG)
- `logs/`: Execution logs

## Validation
Verify outputs exist:
```bash
ls -R data/processed/
ls -R figures/
cat data/raw/manifest.json
```