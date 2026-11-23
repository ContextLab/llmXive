# Quickstart: Phase Transitions in Amorphous Solids Under Shear Stress

## Prerequisites

*   Python 3.11+
*   `pip`
*   Access to the Hugging Face datasets library (for dependencies).

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of four main steps: Data Generation, Preprocessing, Analysis, and Validation.

### Step 1: Generate Synthetic MD Data
Generates valid MD trajectories with physical labels.

```bash
python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/data_generator.py \
  --output data/raw/synthetic_trajectories \
  --num-trajectories 10 \
  --seed 42
```

### Step 2: Preprocessing (Compute $D^2_{min}$)
Computes non-affine displacement and identifies yielding.

```bash
python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/preprocessing.py \
  --input data/raw/synthetic_trajectories \
  --output data/processed/d2_min_trajectory.csv \
  --seed 42
```

### Step 3: Statistical Analysis (Permutation Test)
Aggregates data to shear bands and runs the Permutation Test.

```bash
python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/analysis.py \
  --input data/processed/d2_min_trajectory.csv \
  --output data/processed/permutation_results.json \
  --aggregation shear_band \
  --k 3
```

### Step 4: Validation (Sensitivity Analysis)
Sweeps thresholds and generates the sensitivity table.

```bash
python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/validation.py \
  --input data/processed/d2_min_trajectory.csv \
  --output data/processed/sensitivity_table.csv \
  --threshold-range 0.05
```

### Step 5: Memory Profiling
Measures and reports RAM usage.

```bash
python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/memory_profiler.py \
  --input data/processed/d2_min_trajectory.csv \
  --output data/processed/memory_profile.json
```

## Verifying Results

1.  Check `data/processed/permutation_results.json` for the p-value.
2.  Check `data/processed/sensitivity_table.csv` for the FPR/FNR sweep.
3.  Check `data/processed/memory_profile.json` for peak RAM usage.
4.  Ensure `data/processed/shear_band_stats.csv` exists and contains `shear_band_id`, `mean_D2_min`, `particle_count`.

## Troubleshooting

*   **Memory Error**: Ensure `streaming=True` is used in the data loader (handled automatically in `data_loader.py`).
*   **Missing Data**: If the synthetic generator fails, check the "Verified datasets" block in `research.md` for the correct logic.
*   **Power Warning**: If the dataset has < 30 samples per group, the pipeline will issue a warning but continue.