# Quickstart: Neural Narrative Networks

## Prerequisites
*   Python 3.11+
*   Git
*   Access to GitHub Actions (for CI execution) or a local machine with sufficient RAM.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-595-neural-narrative-networks-brain-inspired
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Execution Workflow

### Step 1: Data Ingestion
Download and preprocess the fMRI and text data.
```bash
python code/01_data_ingestion.py
```
*   **Input**: Verified URLs (OpenNeuro ds000208, ROCStories).
*   **Output**: `data/processed/neural/*.npy`, `data/processed/text/stories_sample.jsonl`.
*   **Validation**: Script exits with error if checksums fail or ROI masks are missing.
*   **Alignment**: Performs semantic alignment of event boundaries.

### Step 2: Model Generation
Generate narratives using the brain-inspired and baseline models.
```bash
python code/02_model_generation.py
```
*   **Input**: `data/processed/text/stories_sample.jsonl`.
*   **Output**: `data/processed/model/brain_inspired_states.npy`, `data/processed/model/baseline_sae_states.npy`.
*   **Note**: Runs on CPU. May take several hours.

### Step 3: RSA Analysis
Compute similarity and perform permutation tests.
```bash
python code/03_rsa_analysis.py
```
*   **Input**: Neural timecourses and model states.
*   **Output**: `data/results/rsa_matrices.csv`, `data/results/permutation_results.json`.
*   **Note**: Runs a sufficient number of label-shuffling permutations. Checks convergence.

### Step 4: Visualization
Generate plots.
```bash
python code/04_visualization.py
```
*   **Output**: `data/results/rsa_heatmap.png`, `data/results/comparison_barplot.png`.

## Testing

Run the contract tests to verify data integrity:
```bash
pytest tests/ -v
```

## Troubleshooting

*   **Memory Error**: If `MemoryError` occurs, reduce the batch size in `code/02_model_generation.py` or enable chunking in `code/01_data_ingestion.py`.
*   **ROI Missing**: If the script halts with "ROI definition failed", verify the `nilearn` Harvard-Oxford atlas is accessible.
*   **Permutation Non-Convergence**: If the p-value variance > 0.001, the result is flagged as "borderline". Check the `data/results/permutation_results.json` for the exact variance.
*   **Alignment Failure**: If semantic alignment fails, the pipeline will log the number of unaligned events and proceed with the common subset only.
