# Quickstart: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Prerequisites

- Python 3.11+
- pip
- git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-982-llmxive-follow-up-extending-dopd-dual-on
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `gym-minigrid`, `numpy`, `scipy`, `pytest`.*

## Running the Experiments

### 1. Run a Single Seed (Debug)
To test the environment and a single training run:
```bash
python code/main.py --seed 42 --regime dopd --steps 1000
```
This will:
- Generate the MDP with seed 42.
- Train the Student using DOPD.
- Evaluate with and without the privileged signal.
- Save logs to `data/raw/`.

### 2. Run the Full Experiment (50 Seeds)
To reproduce the full study:
```bash
python code/main.py --seeds 50 --regimes uniform,dopd,randomized_weight --steps 10000
```
This will:
- Run 50 independent seeds for all regimes.
- Ensure distinct seeds for training (0-49) and evaluation (50-99).
- Aggregate results into `data/processed/`.
- Run the one-tailed Mann-Whitney U test and generate `statistical_summary.json`.

### 3. Verify Results
Check the statistical summary:
```bash
cat data/processed/statistical_summary.json
```
Look for:
- `p_value`: Should be < 0.05 to reject the null hypothesis.
- `effect_size`: If < 0.5, the study is marked as "exploratory".
- `performance_drop`: Compare DOPD vs. Uniform.
- `is_exploratory`: Boolean flag indicating study power.

## Testing

Run the unit and integration tests:
```bash
pytest code/tests/ -v
```
Specific tests:
- `test_division_by_zero_safety`: Verifies FR-002 safety checks.
- `test_distinct_seeds`: Verifies FR-007 seed separation logic.
- `test_advantage_gap_switch`: Verifies min-max normalization fallback.
- `test_baseline_independence`: Verifies baseline seeds are distinct from train/eval.

## Troubleshooting

- **Memory Error**: Reduce grid size in `code/env/privileged_grid.py` (max 10x10).
- **ZeroDivisionError**: Ensure the `safety_checks` in `dopd_distillation.py` are active.
- **Import Error**: Ensure `gym-minigrid` is installed (`pip install gym-minigrid`).
