# The Influence of Visual Complexity on Implicit Bias

## Overview
This project investigates how the visual complexity of background stimuli influences implicit bias scores (D-scores) in an Implicit Association Test (IAT) setting.
The pipeline automates the extraction of visual complexity metrics, experimental data processing, statistical analysis (Permutation Test), and visualization.

## Project Structure
```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis (PCA, Permutation, Sensitivity)
│ ├── data/ # Data loading, processing, and counterbalancing
│ ├── stimuli/ # Image metrics (Edge Density, Entropy, Fractal Dimension)
│ ├── utils/ # Logging, configuration
│ ├── viz/ # Plotting and report generation
│ ├── config.py # Project configuration
│ ├── main.py # Pipeline orchestration
│ └──...
├── data/ # Data directory
│ ├── raw/
│ │ ├── stimuli/ # Input background images
│ │ └── responses/ # Raw IAT response logs
│ ├── processed/ # Intermediate and final processed data
│ └── results/ # Final analysis outputs (JSON, PNG, MD)
├── docs/ # Documentation
├── tests/ # Test suite
└── logs/ # Execution logs
```

## Installation
1. Ensure Python >= 3.11 is installed.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage
Run the full pipeline:
```bash
python code/main.py
```
For CI/testing with synthetic data (null-effect mode):
```bash
python code/main.py --null-effect
```

## Data Flow
This section details the dependency chain for assigning stimulus sets to complexity conditions, ensuring reproducibility and methodological integrity.

### Step 1: Complexity Quantification (T017a-3)
**Input**: Validated images from `data/raw/stimuli/`.
**Process**:
1. Calculate metrics: Edge Density, Entropy, Fractal Dimension (`code/stimuli/metrics.py`).
2. Perform PCA to derive a single complexity score (PC1).
3. Apply Median Split (q=2) on PC1 scores to categorize images.
 - **Tie-Breaking**: Values equal to the median are assigned to 'Low'.
**Output**: `data/processed/complexity_scores.csv`
**Columns**: `filename`, `edge_density`, `entropy`, `fractal_dim`, `complexity_category` (values: 'Low', 'High').

### Step 2: Stimulus-to-Set Mapping (T027a-Map)
**Input**: `data/processed/complexity_scores.csv`.
**Process**:
1. Iterate through the complexity categories.
2. Map 'Low' complexity images to `stimulus_set_id` = 'SetA'.
3. Map 'High' complexity images to `stimulus_set_id` = 'SetB'.
**Output**: `data/processed/stimulus_set_mapping.csv`
**Columns**: `filename`, `stimulus_set_id`.

### Step 3: Counterbalance Assignment (T027a)
**Input**:
1. `data/processed/stimulus_set_mapping.csv` (derived from Step 2).
2. `data/raw/responses/participants.csv` (or synthetic IDs if `--null-effect`).
**Process**:
1. Generate a list of participant IDs.
2. Apply a seeded random shuffle (seed=42).
3. Assign `session_order` ('Low-High' or 'High-Low') and `stimulus_set_id` based on the shuffle.
 - **Constraint**: The `stimulus_set_id` assignment MUST align with the mapping from Step 2.
 - Participants assigned to 'SetA' will encounter 'Low' complexity stimuli in their first session (if order is Low-High) or second (if High-Low).
 - Participants assigned to 'SetB' will encounter 'High' complexity stimuli.
**Output**: `data/processed/counterbalance_assignment.csv`
**Columns**: `participant_id`, `session_order`, `stimulus_set_id`.

### Step 4: Aggregation (T026b-3)
**Input**:
1. `data/processed/d_scores_raw.csv` (Calculated D-scores).
2. `data/processed/counterbalance_assignment.csv`.
3. `data/processed/complexity_scores.csv`.
**Process**:
1. Join D-scores with Counterbalance data on `participant_id` to retrieve `stimulus_set_id`.
2. Join with Complexity Scores to resolve `complexity_condition` (Low/High) based on the `stimulus_set_id`.
**Output**: `data/processed/aggregated_d_scores.csv`
**Usage**: This final dataset drives the Permutation Test (T033) and Visualization (T037).

## API Reference
See individual module docstrings in `code/` for detailed function signatures.
- `code/analysis/permutation.py`: `run_permutation_test`, `calculate_effect_size`
- `code/data/process.py`: `filter_trials`, `calculate_d_score`
- `code/stimuli/metrics.py`: `calculate_edge_density`, `calculate_entropy`, `calculate_fractal_dim`

## License
MIT License