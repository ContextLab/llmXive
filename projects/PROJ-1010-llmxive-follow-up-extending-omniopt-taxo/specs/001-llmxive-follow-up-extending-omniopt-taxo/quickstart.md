# Quickstart: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

## Prerequisites

-   Python 3.11+
-   Git
-   ~14 GB free disk space (for temporary dataset shards and models)
-   ~8 GB RAM (recommended for smooth operation, though 7GB is the hard limit)

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `torch` is installed in CPU mode (no CUDA required for this pipeline):
    ```bash
    python -c "import torch; print(torch.__version__); print('CPU only:', not torch.cuda.is_available())"
    ```

## Data Preparation

1.  **Download OmniOpt Lookup**:
    Ensure `data/omniopt_lookup.json` exists. If not, generate it from the published OmniOpt tables manually and place it in the `data/` directory.

2.  **Verify Dataset Access**:
    The pipeline will automatically stream `TinyImageNet` from Hugging Face. No manual download is required.
    ```bash
    python -c "from datasets import load_dataset; ds = load_dataset('Multimodal-Fatima/TinyImagenet_train', split='train', streaming=True); print(next(iter(ds)))"
    ```

## Running the Pipeline

Execute the full pipeline (Extraction -> Labeling -> Correlation Analysis):

```bash
python main_pipeline.py
```

### Expected Output

-   `data/processed/spectral_features.csv`: Extracted spectral signatures (Condition Number, Spectral Entropy).
-   `data/processed/labeled_dataset.json`: Merged dataset with optimizer labels.
-   `data/processed/results.json`: Correlation metrics (Spearman rho, p-values).
-   Logs printed to `stdout` indicating progress and any excluded samples.

### Running Individual Steps

-   **Extract Spectral Features Only**:
    ```bash
    python spectral_extractor.py --output data/processed/spectral_features.csv
    ```
-   **Label Data Only**:
    ```bash
    python label_mapper.py --input data/processed/spectral_features.csv --lookup data/omniopt_lookup.json --output data/processed/labeled_dataset.json
    ```
-   **Analyze Correlations Only**:
    ```bash
    python correlation_analyzer.py --input data/processed/labeled_dataset.json --output data/processed/results.json
    ```

## Troubleshooting

-   **Memory Error**: If `MemoryError` occurs, reduce the number of samples in the `main_pipeline.py` configuration (e.g., `SAMPLE_SIZE=500`).
-   **Missing OmniOpt Label**: If a model is excluded, check `logs/exclusions.log` to see which `model_id` was missing from the lookup table. The system will attempt to re-run the benchmark for that entry if time permits.
-   **Numerical Instability**: If `condition_number` is `inf`, check the regularization epsilon in `spectral_extractor.py`.

## Validation

To verify the results:
1.  Check `data/processed/results.json` for `significance: true` (Bonferroni-corrected p < 0.05).
2.  Verify `spearman_rho` is non-zero and in the expected direction (e.g., higher entropy -> Adam).
3.  Run the unit tests:
    ```bash
    pytest tests/
    ```
