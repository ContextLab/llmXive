# Quickstart: Evaluating the Impact of LLM-Generated Code on Memory Usage

## Prerequisites

- Python 3.11+
- ≤ 7 GB RAM available
- Git
- Internet access (for HuggingFace dataset download)

## Installation

1. **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-395-evaluating-the-impact-of-llm-generated-c
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *`torch` is pinned to the CPU‑only build.*

## Configuration

Edit `code/config.yaml` to set:

- `dataset_choice`: `"humaneval"` (exclusive)
- `random_seed`: `42`
- `num_problems`: `30`  # Target sample size for paired analysis
- `model_name`: `"microsoft/Phi-3-mini-4k-instruct"` (or fallback TinyLlama‑1.1B)

## Running the Pipeline

### 1. Download Data
```bash
python code/download_data.py
```
*Downloads HumanEval to `data/raw/` and records checksums.*

### 2. Generate LLM Solutions
```bash
python code/generate_llm.py
```
*Generates solutions for the selected 30 problems ([deferred] per problem on a 2‑core runner).*

### 3. Profile Memory
```bash
python code/profile_memory.py
```
*Executes both LLM and human solutions, records memory/time, handles failures.*

### 4. Extract Features
```bash
python code/extract_features.py
```
*Computes LOC, cyclomatic complexity, and import count.*

### 5. Statistical Analysis
```bash
python code/analyze_stats.py
```
*Runs permutation test on Efficiency Score, chi‑square on failure rates, and regression on raw peak memory.*

## Verification

1. Verify `data/processed/results.csv` contains a dataset of LLM‑human pairs (each with a status column).
2. Check `data/processed/statistical_results.json` for entries `p_value_corrected` for both Efficiency and Reliability tests.
3. Run the test suite:
    ```bash
    pytest tests/
    ```

## Troubleshooting

- **OOM**: If the model exceeds RAM, edit `config.yaml` to use the smaller fallback model.
- **Timeout**: Generation or execution exceeding their limits are logged and counted as failures.
- **Missing Human Reference**: HumanEval always provides executable human solutions; if a problem is skipped, it is reported in the log.
