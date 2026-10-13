# Quickstart: The Impact of Bounded Confidence on Opinion Polarization Speed

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- Git

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-672-the-impact-of-bounded-confidence-on-opin
 ```

2. **Create and activate a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the pipeline

The pipeline consists of three sequential steps. Run them in order to reproduce the study.

### Step 1: Generate Networks

Generates multiple instances of each topology (ER, BA, WS).
```bash
python -m code.generate_networks --topology ER --instances 1 --seed 0
```

**Verification**: The command creates the files

- `data/raw/networks/ER_0000.edgelist`
- `data/raw/networks/metadata_ER_0000.json`

without errors.

### Step 2: Run Simulations

Executes the HK model for all networks and ε values.
```bash
python code/simulate_hk.py \
 --networks data/raw/networks/ \
 --epsilon-start 0.05 \
 --epsilon-end 0.50 \
 --epsilon-step 0.05 \
 --seeds 50 \
 --output data/raw/simulations/
```

### Step 3: Analyze Results

Fits power‑law models and runs regressions.
```bash
python code/analyze_scaling.py \
 --simulations data/raw/simulations/ \
 --networks data/raw/networks/ \
 --output data/processed/
```

## Verification

To verify that the installation and the first step work correctly:

```bash
# Run the verification command from Step 1
python -m code.generate_networks --topology ER --instances 1 --seed 0

# Check that the expected files exist
ls data/raw/networks/ER_0000.edgelist
ls data/raw/networks/metadata_ER_0000.json
```

If both commands list a file without error, the quick‑start verification has passed.
