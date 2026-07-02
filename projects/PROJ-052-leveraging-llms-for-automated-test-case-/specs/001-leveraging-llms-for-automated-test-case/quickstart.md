# Quickstart: Automated Test Case Generation Pipeline

## Prerequisites
- GitHub Actions Runner (Free Tier) or local environment with:
  - Python 3.11+
  - Java 17+
  - Maven or Gradle (for target projects, if building manually)
  - 7GB+ RAM available
- Access to HuggingFace (for dataset download).

## Setup

### 1. Clone and Install Dependencies
```bash
git clone <repo-url>
cd specs/001-llm-test-generation
pip install -r code/requirements.txt
```
*Note: Ensure `llama-cpp-python` is installed with CPU-only wheels (`CMAKE_ARGS="-DLLAMA_BLAS=OFF"`).*

### 2. Download Data
Run the data loader to fetch the verified Defects4J dataset:
```bash
python code/data_loader.py --download --source "chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3"
```
*This creates `data/raw/defects4j_prompts.parquet`.*

### 3. Configure Execution
Edit `code/config.py`:
- `SAMPLE_LIMIT`: Set to a small number (e.g., 5) for initial testing.
- `TIMEOUT_SECONDS`: 30 (default).
- `MAX_RETRIES`: 3.
- `MODEL_PATH`: Path to the downloaded Phi-2 GGUF file (e.g., `models/phi-2.Q4_K_M.gguf`).

## Running the Pipeline

### Full Execution
```bash
python code/main.py
```
This will:
1. Load data.
2. Generate tests (LLM).
3. Compile and execute (Java/JaCoCo).
4. Run statistical analysis.
5. Output `data/processed/coverage_metrics.csv` and `data/processed/analysis_results.json`.

### Individual Steps
- **Generate Only**: `python code/main.py --step generate`
- **Execute Only**: `python code/main.py --step execute` (requires pre-generated tests)
- **Analyze Only**: `python code/main.py --step analyze` (requires `coverage_metrics.csv`)

## Verification
Check `data/processed/coverage_metrics.csv` for entries.
Verify `data/processed/analysis_results.json` contains a `p_value` and `test_type`.
Run `pytest` to ensure all output files conform to `contracts/` schemas.
