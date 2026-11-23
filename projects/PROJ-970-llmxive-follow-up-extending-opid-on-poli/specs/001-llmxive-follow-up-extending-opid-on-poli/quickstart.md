# Quickstart: OPID Critical-First Routing Complexity Analysis

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `networkx`, `numpy`, `pandas`, `scipy`, `statsmodels`, `pytest`.*

## Running the Simulation

### 1. Generate Synthetic Environments
Generate the graph suite for all three tiers, including the train/validation split.
```bash
python -m src.environment.graph_generator --output data/raw/synthetic_graphs
```
*This creates JSON files for Tier 1, Tier 2, and Tier 3 graphs, marking a majority portion as 'train' and a minority portion as 'validation'.*

### 2. Run the Full Experiment
Execute the simulation sweep across all thresholds and tiers.
```bash
python -m src.simulation.runner --config src/config.py --output data/processed/episode_results.csv
```
*This will run [deferred] episodes per setting (11 thresholds × 3 tiers) on the **training** graphs. If the estimated time exceeds 6 hours, it will gracefully reduce N.*

### 3. Analyze Results
Perform statistical analysis (GLM, Quadratic Regression) and generate the final metrics.
```bash
python -m src.analysis.aggregation --input data/processed/episode_results.csv --output data/processed/aggregated_metrics.csv
python -m src.analysis.regression --input data/processed/aggregated_metrics.csv
```

## Verification

To verify the implementation, run the unit tests:
```bash
pytest tests/unit/ -v
```

To run the integration test (full loop with small N):
```bash
pytest tests/integration/test_full_loop.py -v
```

## Expected Output

- `data/processed/episode_results.csv`: A CSV with a scalable number of rows (depending on N).
- `data/processed/aggregated_metrics.csv`: A summary table with multiple rows (11 thresholds × 3 tiers), including rigidity and cost-benefit metrics.
- Console output: Progress bars and final statistical significance results (p-values for quadratic terms, inflection points).