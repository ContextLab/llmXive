# Quickstart: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

## Prerequisites
*   Python 3.11+
*   7GB+ RAM (CPU-only execution)
*   HuggingFace CLI (`huggingface-cli`)
*   Linting/Formatting tools: `ruff`, `black`

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <repo-dir>
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `transformers`, `datasets`, `torch`, `bitsandbytes`, `scikit-learn`, `statsmodels`, `pyyaml`, `ruff`, `black`.*

4.  **Setup Linting & Formatting**:
    ```bash
    ruff check src/
    black --check src/
    ```
    *Configuration files `.ruff.toml` and `pyproject.toml` define the rules.*

5.  **Download the AIME dataset**:
    ```bash
    python src/data/loaders.py --download
    ```
    *This script uses `datasets` to download the verified AIME dataset to `data/raw/`.*

## Running the Experiments

### 1. Compute Implicit Reward
```bash
python src/data/preprocessor.py --compute-reward
```
*Computes the log-ratio reward signal for the AIME subset using the teacher checkpoints.*

### 2. Train MoE Student (Direct-OPD)
```bash
python src/models/moe_student.py --regime direct-opd
```
*Trains the MoE student to maximize the implicit reward. Uses batch size 1 and int8 quantization.*

### 3. Train MoE Baseline
```bash
python src/models/moe_student.py --regime baseline
```
*Trains the MoE student using standard distillation (teacher distribution only).*

### 4. Train SSM Student (Direct-OPD)
```bash
python src/models/ssm_student.py --regime direct-opd
```
*Trains the SSM student on CPU.*

### 5. Train SSM Baseline
```bash
python src/models/ssm_student.py --regime baseline
```

### 6. Run Statistical Analysis
```bash
python src/analysis/stats_utils.py
```
*Performs Wilcoxon signed-rank tests with Bonferroni correction and generates the comparative summary.*

### 7. Generate Report
```bash
python src/analysis/summary_generator.py
```
*Outputs the final comparative summary text block to `artifacts/summary.md`.*

## Verification
*   **Linting**: `ruff check src/`
*   **Formatting**: `black src/`
*   **Tests**: `pytest tests/`
*   **Schema Validation**: `pytest tests/contract/`

## Troubleshooting
*   **OOM Error**: The `memory_guard.py` module will automatically reduce batch size. If it reaches the floor (1), the run will halt with an error.
*   **Missing Dataset**: Ensure `datasets` is installed and your HuggingFace token is configured.
*   **Missing RL Checkpoint**: If the 'Post-RL' checkpoint is not found, the script will halt and report the missing artifact.
