# Quickstart: Evaluating the Explainability of LLM-Based Bug Fixes

## Prerequisites

- Python 3.11 or higher
- 7 GB+ available RAM
- 14 GB+ available disk space
- HuggingFace account (for CodeLlama access)

## Setup

### 1. Clone and Install

```bash
cd projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Authenticate with HuggingFace

```bash
huggingface-cli login
# Enter token for codellama/CodeLlama-Instruct-hf access
```

### 3. Verify Dataset Access

```bash
python 01_download_data.py --verify-only
# Should output: "DefectsJ v2.0 verified: checksums match"
```

## Run Pipeline

### Full End-to-End (a set of bugs, estimated computational time on CPU)

```bash
# Download dataset
python 01_download_data.py --download

# Generate patches
python 02_generate_patches.py --sample-size 50 --seed 42

# Execute tests
python 03_execute_tests.py --timeout 60

# Extract explainability scores
python 04_extract_attention.py
python 05_compute_saliency.py
python 06_compute_bleu_rouge.py

# Statistical analysis
python 07_statistical_analysis.py
```

### Process Single Bug (for testing)

```bash
python 02_generate_patches.py --bug-id Defects4J-Lang-1 --seed 42
python 03_execute_tests.py --bug-id Defects4J-Lang-1 --timeout 60
python 04_extract_attention.py --bug-id Defects4J-Lang-1
python 05_compute_saliency.py --bug-id Defects4J-Lang-1
python 06_compute_bleu_rouge.py --bug-id Defects4J-Lang-1
```

## Validate Outputs

### Contract Tests

```bash
cd tests/contract/
pytest
# Should pass all schema validations
```

### Reproducibility Check

```bash
# Re-run on fresh environment
rm -rf data/derived/ explanations/
python 01_download_data.py --download
python 02_generate_patches.py --sample-size 50 --seed 42
# Compare outputs with previous run (checksums should match)
```

## Expected Outputs

| Output | Location | Format |
|--------|----------|--------|
| Dataset | `data/defects4j/raw/` | Parquet |
| Patches | `data/derived/patches.csv` | CSV |
| Correctness labels | `data/derived/correctness.csv` | CSV |
| Explainability scores | `data/derived/scores.csv` | CSV |
| Statistical results | `data/derived/statistical_results.csv` | CSV |
| Attention heatmaps | `explanations/*_attention.png` | PNG |
| Saliency arrays | `explanations/*_saliency.npy` | NumPy |
| Rationales | `explanations/*_rationale.txt` | Text |
| Metadata | `explanations/*_metadata.json` | JSON |

## Troubleshooting

### OOM Error (7 GB RAM limit)

```bash
# Reduce sample size
python 02_generate_patches.py --sample-size 25 --seed 42
```

### Test Suite Timeout

```bash
# Increase timeout (not recommended; violates spec)
# Or exclude slow bugs from analysis
python 03_execute_tests.py --timeout 60 --exclude-bugs slow-bugs.csv
```

### Model Download Failure

```bash
# Ensure HuggingFace token is set
export HF_TOKEN=your_token_here
huggingface-cli login
```
