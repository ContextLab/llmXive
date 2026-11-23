# Quickstart: The Impact of Bounded Confidence on Opinion Polarization Speed

## Prerequisites
- Python 3.11+
- `pip`
- Git

## Installation
1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
 ```

2. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The research pipeline consists of three sequential steps.

### Step 1: Generate Networks
Generates reproducible ensembles of synthetic networks.
```bash
python -m code.generate_networks --instances 50 --seed 0
```
**Verification**:
To verify a single instance:
```bash
python -m code.generate_networks --topology ER --instances 1 --seed 0
```
This creates `data/raw/networks/ER_0000.edgelist` and `data/raw/networks/metadata_ER_0000.json`.

### Step 2: Run Simulations
Executes the HK model sweep.
```bash
python -m code.run_batch \
 --networks data/raw/networks/ \
 --output data/raw/simulations/ \
 --epsilon-start 0.05 \
 --epsilon-end 0.50 \
 --epsilon-step 0.05 \
 --seeds 50
```

### Step 3: Analyze Results
Fits power laws and performs regressions.
```bash
python -m code.analyze_scaling \
 --simulations data/raw/simulations/ \
 --networks data/raw/networks/ \
 --output data/processed/
```

## Verification & Testing
Run the full test suite:
```bash
pytest tests/ -v
```
