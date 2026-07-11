# Quickstart: llmXive Follow-up: Extending "A Stylometric Application of Large Language Models"

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available
- Access to HuggingFace Datasets (no token required for public dataset)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-809-llmxive-follow-up-extending-a-stylometri
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
    *Note: `requirements.txt` pins `datasets`, `scikit-learn`, `scipy`, `numpy`, `pandas`, `pyyaml`.*

4.  **Setup Contracts**:
    The contract schemas in `specs/.../contracts/` are the source of truth. Copy them to the code directory for validation:
    ```bash
    cp specs/001-llmxive-followup/contracts/*.yaml code/contracts/
    ```

## Execution

The pipeline is executed via the `main.py` script. It handles data ingestion, training, evaluation, and reporting in a single run.

### Run Full Pipeline
```bash
cd code
python main.py
```

**What happens**:
1.  **Ingestion**: Downloads and filters the `arXiv` dataset (cs.CL, physics.gen-ph, q-bio.QM, with fallback) to a representative subset of authors via stratified sampling.
2.  **Preprocessing**: Cleans text and splits into train/test.
3.  **Training**: Trains n-gram models (n=4, 5, 6) for each author (with sparsity checks).
4.  **Evaluation**: Computes perplexity matrix (primary: n=5) and classification accuracy.
5.  **Baseline**: Trains function-word Naive Bayes and runs McNemar's test.
6.  **Robustness**: Generates hybrid abstracts (author swap + random swap control) and measures accuracy drop.
7.  **State Update**: Updates `state/projects/...yaml` with artifact hashes.
8.  **Output**: Saves results to `artifacts/metrics/final_results.json`.

### Run Specific Phase (Debugging)

- **Only Ingestion & Preprocessing**:
  ```bash
  python main.py --phase ingestion
  ```
- **Only Training**:
  ```bash
  python main.py --phase training
  ```
- **Only Evaluation**:
  ```bash
  python main.py --phase evaluation
  ```

## Verification

After the pipeline completes, verify the outputs:

1.  **Check Results**:
    ```bash
    cat ../artifacts/metrics/final_results.json
    ```
    Ensure `is_significant` is `true` (if data supports it) and `hybrid_accuracy_drop` is reported.

2.  **Check Perplexity Matrix**:
    ```bash
    head -n 5 ../artifacts/metrics/perplexity_matrix.csv
    ```

3.  **Run Contract Tests**:
    ```bash
    pytest tests/contract/
    ```
    This validates that all output artifacts match the schemas defined in `contracts/` (copied from `specs/`).

## Troubleshooting

- **Error: "DataInsufficientError: Less than 20 authors found"**
  - *Cause*: The arXiv dataset subset does not contain enough authors with $\ge$ 10 abstracts in the specified categories, even with fallback.
  - *Fix*: This is a data limitation. The pipeline halts gracefully. No code fix is possible without changing the dataset or relaxing constraints (which violates the spec).

- **Error: "MemoryError"**
  - *Cause*: N-gram state space is too large for the runner's RAM.
  - *Fix*: Reduce the max n-gram order in `code/utils.py` (e.g., set `MAX_N_ORDER = 4`) and re-run.

- **Error: "ImportError: No module named 'datasets'"**
  - *Cause*: Dependencies not installed.
  - *Fix*: Run `pip install -r code/requirements.txt`.