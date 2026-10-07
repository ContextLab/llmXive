# Quickstart: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

## Prerequisites

- Python 3.11 or higher
- pip (package manager)

## Installation

1. Navigate to the project directory:
   ```bash
   cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Generate Synthetic Trajectories

```bash
python code/generate_trajectories.py --num-trajectories [REDACTED] --output data/raw/trajectories.json --seed 42

The research question and method remain as defined in the original plan. References are preserved verbatim.
```

- **Output**: `data/raw/trajectories.json` (contains 500 trajectories)
- **Validation**: The script will automatically validate entropy levels (within a specified tolerance) and check the count matches the target sample size. If validation fails, it exits with code 1.

### Step 2: Validate Trajectories (Explicit Gate)

```bash
python code/validate_trajectories.py --input data/raw/trajectories.json
```

- **Action**: Checks that exactly 500 trajectories exist and that all critical evidence blocks meet the entropy tolerance.
- **Exit Code**: 0 if valid, 1 if invalid. **Do not proceed if exit code is 1.**

### Step 3: Run Agent Simulation

```bash
python code/simulate_agent.py --input data/raw/trajectories.json --output data/logs/simulation_results.csv --seed 42
```

- **Output**: `data/logs/simulation_results.csv` (contains simulation logs)
- **Note**: This step runs the agent with multiple sampled horizons per trajectory.

### Step 4: Analyze Results

```bash
python code/analyze_results.py --input data/logs/simulation_results.csv --output results/regime_map.png
```

- **Output**:
  - Console: Regression coefficients and p-values.
  - File: `results/regime_map.png` (3D surface plot).

## Verification

To verify the pipeline:

1. Check that `data/raw/trajectories.json` exists and is valid JSON.
2. Check that `data/logs/simulation_results.csv` has the expected columns.
3. Check that `results/regime_map.png` is a valid PNG file.

## Troubleshooting

- **Memory Error**: If you encounter memory errors, reduce the number of trajectories (e.g., `--num-trajectories 100`) for testing.
- **Entropy Validation Failed**: Ensure the `generate_trajectories.py` script is using the correct entropy calculation method (UTF-8 byte-level) and the tolerance check is correct.
- **Count Validation Failed**: Ensure the generator is creating trajectories.