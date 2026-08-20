# Quickstart: llmXive follow-up: extending "AlayaWorld"

## Prerequisites

-   Python 3.11+
-   A GitHub Actions runner with a small number of vCPUs and limited RAM (or a local machine with similar constraints).
-   (Optional) AlayaWorld model weights in `data/` (if not using the mock generator).

**Important**: This project uses a **synthetic validation** approach. The default mode is "Mock-only", which uses a deterministic mock video generator (the "Naive Generator") to simulate AlayaWorld behavior with *intentionally injected generative errors*. The "Semantic Drift Score" in this mode measures the efficacy of the correction mechanism against these injected errors, not the performance of the real AlayaWorld model. If real AlayaWorld weights are provided, the "Real Model Run" mode can be used, but the metrics are *not directly comparable* to the "Mock-only" mode without normalization.

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or venv\Scripts\activate  # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/requirements.txt
    ```
    *Note: The requirements file pins `opencv-python-headless` and `torch` (CPU version).*

## Running the Pipeline

### 1. Generate Mock Data (Default Mode)
Run the mock generator to create deterministic test sequences with injected generative errors:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode mock --seeds 10 --sequences-per-seed 10
```
This will generate `data/processed/symbolic_logs/` and mock video frames in `data/raw/`.

### 2. Run Baseline (Naive Generator)
Run the baseline experiment without correction tokens:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode baseline --seeds 10
```
*Output*: `data/processed/metrics/baseline_metrics.csv` (100 sequences total)

### 3. Run Hybrid (Correction)
Run the experiment with the symbolic correction loop:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode hybrid --seeds 10
```
*Output*: `data/processed/metrics/hybrid_metrics.csv` (100 sequences total)

### 4. Validate CV Accuracy
Run the validation step on the annotated subset:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode validate-cv
```
*Output*: Prints the accuracy to stdout. Note: Accuracy is expected to be < 85% due to the injected errors.

### 5. Statistical Analysis
Compare the results:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode analyze
```
*Output*: Prints the paired t-test results (p-value, mean reduction) and resource usage summary.

### 6. (Optional) Real Model Run
If AlayaWorld weights are provided in `data/`, you can run the real model:
```bash
python projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/main.py --mode real --seeds 10
```
*Note*: The metrics from this mode are *not directly comparable* to the "Mock-only" mode. The research conclusions are strictly limited to the "Mock-only" validation unless real weights are available and the metrics are normalized.

## Troubleshooting

-   **Memory Error**: If the process exceeds available RAM, reduce the `--sequence-length` or ensure `opencv-python-headless` is installed (not the full GUI version).
-   **CV Accuracy Low**: If the validation accuracy is < 85%, this is expected due to the injected generative errors. It is a feature of the experiment, not a bug.
-   **Slow Execution**: The mock generator is designed to be fast. If using real weights, ensure the model is loaded in CPU mode (`device='cpu'`).
