# Quickstart: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

## 1. Prerequisites

*   Python 3.11+
*   Git
*   GitHub Actions (for CI execution) or a local environment with ≥7GB RAM.

## 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: Ensure `torch` is installed without CUDA support (e.g., `pip install torch --index-url https://download.pytorch.org/whl/cpu`).*

## 3. Data Preparation

The pipeline automatically downloads the verified datasets on first run.

1.  **Run the data loader**:
    ```bash
    python code/data_loader.py --download
    ```
    This will:
    *   Fetch the LibriSpeech and CORAA subsets.
    *   Compute checksums.
    *   Store raw data in `data/raw/`.

2.  **Verify data integrity**:
    ```bash
    python code/data_loader.py --verify
    ```

## 4. Running the Stress Test Pipeline

Execute the full pipeline (distortion generation, ASR inference, collapse detection, regression):

```bash
python code/main.py --config code/config.yaml
```

**Configuration Options** (in `code/config.yaml`):
*   `sample_size`: Number of clips to process (default: 100 for testing).
*   `models`: List of ASR models to test (e.g., `["whisper-tiny"]`).
*   `threshold`: SSS collapse threshold (default: 0.5).
*   `sensitivity_sweep`: Boolean to run the threshold sweep (0.40-0.60).

## 5. Resource Monitoring & CI Enforcement (SC-004)

To ensure the pipeline runs within the 7GB RAM and 6-hour limits:

1.  **Manual Check**:
    ```bash
    python code/monitor_resources.py
    ```
    This script logs current resource usage.

2.  **CI Enforcement**:
    The GitHub Actions workflow includes a step:
    ```yaml
    - name: Check Resource Constraints
      run: python code/monitor_resources.py --check-limit --max-rss 7000000000
    ```
    If RSS exceeds 7GB, this step **fails the job**.

## 6. Viewing Results

*   **Stress Curves**: `data/derived/stress_curves.parquet`
*   **Collapse Points**: `data/derived/collapse_points.parquet`
*   **Regression Results**: `data/derived/regression_results.json`
*   **Plots**: `data/derived/figures/` (e.g., `collapse_distribution.png`, `interaction_vector.png`)

## 7. Versioning & State Update (Principle V)

After a successful run, update the project state file with content hashes:

```bash
python code/hash_updater.py
```
This script computes hashes for all `data/derived/` artifacts and updates `state/projects/PROJ-844-llmxive-follow-up-extending-mega-asr-tow.yaml`.

## 8. Validation & Testing

1.  **Run Unit Tests**:
    ```bash
    pytest tests/unit/
    ```

2.  **Run Contract Tests** (validates data schemas):
    ```bash
    pytest tests/contract/
    ```

3.  **Validate SSS Metric** (FR-011):
    ```bash
    python code/analysis.py --validate-sss
    ```

4.  **Test Multiple Comparison Correction** (FR-008):
    ```bash
    pytest tests/contract/test_multiple_comparison.py
    ```

## 9. Troubleshooting

*   **Memory Error**: Reduce `sample_size` in `config.yaml` or process in smaller chunks.
*   **Runtime Error**: Ensure `torch` is the CPU version. Check `pip list | grep torch`.
*   **Dataset Missing**: Verify internet connection and that the verified URLs in `research.md` are accessible.