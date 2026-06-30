# Quickstart: Visual Detail and False Memory Susceptibility

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a terminal (Linux/macOS/WSL)

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-317-the-impact-of-visual-detail-on-false-mem
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of three main stages: **Stimulus Generation**, **Session Simulation**, and **Analysis**.

### 1. Generate Stimuli

This step creates the baseline images (mock) and their manipulated versions.

```bash
python code/cli.py generate-stimuli --count 30 --seed 42
```

-   `--count`: Number of baseline images to generate.
-   `--seed`: Random seed for reproducibility.
-   **Output**: Images saved to `data/stimuli/`, metadata to `data/stimuli_metadata/`.

### 2. Simulate Participants

This step runs the participant interface simulation to generate response data.

```bash
python code/cli.py simulate-sessions --n-sessions 60 --seed 42
```

-   `--n-sessions`: Number of simulated participants.
-   **Output**: Response logs saved to `data/responses/`.

### 3. Run Analysis

This step performs the repeated-measures ANOVA and generates visualizations.

```bash
python code/cli.py run-analysis --output data/processed/results.json
```

-   **Output**: JSON results and PNG plots saved to `data/processed/`.

## Verification

To verify the setup:

1.  Check that `data/stimuli/` contains at least 30 baseline images and 60 manipulated images.
2.  Check that `data/responses/` contains JSON files for 60 sessions.
3.  Run the unit tests:
    ```bash
    pytest tests/unit/
    ```

## Troubleshooting

-   **Memory Error**: If running on low RAM, reduce `--count` or `--n-sessions`.
-   **Missing Dependencies**: Ensure `requirements.txt` is installed in the virtual environment.
-   **Checksum Mismatch**: If data files have been modified, delete `data/` and re-run the pipeline.
