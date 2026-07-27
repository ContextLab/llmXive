# Quickstart: Visual Detail and False Memory Susceptibility

## Prerequisites

*   Python 3.11+
*   `pip`
*   Git

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-317-the-impact-of-visual-detail-on-false-mem

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline (CI Validation)

This command runs the pipeline with the **Pre-bundled Subset** to validate the logic without external dependencies.

```bash
# 1. Generate stimuli from pre-bundled subset
python code/stimuli/generator.py --mode pre-bundled --count 30 --seed 42

# 2. Run simulated participant sessions (mock data for validation)
python code/participants/interface.py --mode mock --n-sessions 60

# 3. Run power analysis (should pass gate if N >= 50)
python code/analysis/power.py

# 4. Run ANOVA and generate visualization
python code/analysis/anova.py
python code/analysis/viz.py --output data/analysis/results.png
```

## Running the Full Study (Requires Visual Genome Verification)

*Note: Requires Visual Genome to be verified in the dataset list or manually downloaded.*

```bash
# 1. Fetch real stimuli (if verified)
python code/utils/data_loader.py --source visual_genome --limit 30

# 2. Run participant sessions (requires actual recruitment or mock mode)
python code/participants/interface.py --mode real --n-sessions 60

# 3. Analyze
python code/analysis/anova.py
```

## Verification

*   Check `data/stimuli/` for generated images.
*   Check `data/responses/` for participant data.
*   Check `data/analysis/results.png` for the plot.