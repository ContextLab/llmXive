# Quickstart: Evaluating the Impact of Code Generation Models on Developer Productivity

**Branch**: `001-code-gen-productivity` | **Date**: 2024-01-15

## Prerequisites

- Python 3.11+
- Git
- Modern web browser (Chrome/Firefox/Edge)
- Access to GitHub (for experiment hosting)

## Installation

```bash
# Clone repository
git clone
cd evaluating-code-gen-productivity

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt

# Verify installations
python -c "import flask; import radon; import coverage; import pylint; import scipy; print('All dependencies OK')"
```

## Configuration

### 1. Dataset Setup

```bash
# Download HumanEval (official GitHub repo)
mkdir -p data/raw/humaneval
cd data/raw/humaneval
git clone https://github.com/openai/human-eval.git.
# Record exact commit hash
COMMIT_HASH=$(git rev-parse HEAD)
echo "HumanEval commit: $COMMIT_HASH" > metadata.txt
cd../..

# Download Codeforces problems (via API)
# Note: Filter for medium difficulty problems; record API snapshot date
mkdir -p data/raw/codeforces
# Use Codeforces API to fetch medium difficulty problems
# Example: https://codeforces.com/problemset?tags=implementation,dp&order=BY_RATING_ASC
wget "https://codeforces.com/api/problemset.problems" -O data/raw/codeforces/problems.json
# Record API snapshot date
echo "Codeforces snapshot: $(date -Iseconds)" >> data/raw/codeforces/metadata.txt

# Generate checksums per Constitution III
find data/raw -type f -exec sha256sum {} \; > data/metadata.yaml
```

### 2. Model Setup (CPU-Only)

```bash
# StarCoder for Python (verified CPU compatibility)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers accelerate
python -c "from transformers import AutoModelForCausalLM; print('Transformers installed')"

# JaCoText for Java - NO verified source (see research.md)
# Option 1: Use StarCoder for both languages
# Option 2: Wait for JaCoText verification
# TODO: Update when JaCoText source verified or spec changed
# pip install jacotext-cpu # Placeholder - NOT VERIFIED

# Verify model sizes
python -c "
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('bigcode/starcoder')
print(f'StarCoder size: {sum(p.numel() for p in model.parameters()) * model.get_input_embeddings().weight.element_size() / 1e9:.2f} GB')
"
# Must output: ≤1.0 GB
```

### 3. Experiment Configuration

```bash
# Set random seed for reproducibility
export RANDOM_SEED=42

# Configure experiment parameters
cat > config.yaml <<EOF
experiment:
 num_participants: a representative cohort
 problems_per_condition: 2
 condition_order: "counterbalanced"
 timeout_sec: 60
 llm_timeout_sec: 30
 max_dropout_rate: 0.20

models:
 java: "jacotext" # See research.md for gap
 python: "starcoder"

analysis:
 correction_method: "holm"
 alpha: 0.05
 ci_precision: 0.01
EOF
```

## Running the Experiment

### 1. Start Experiment Interface

```bash
cd code/experiment
python app.py --host 0.0.0.0 --port 5000
```

### 2. Participant Flow

1. Participant accesses `http://<SERVER>:5000`
2. Informed consent screen displayed
3. Upon consent, participant enters unique ID
4. Randomized condition order assigned
5. Problems presented sequentially
6. Code submissions streamed to server
7. Session completed → data logged

### 3. Quality Assessment Pipeline

```bash
cd code/quality
python pass_rate.py --input data/derived/submissions.json --output data/derived/metrics.json
python complexity.py --input data/derived/submissions.json --output data/derived/metrics.json
python coverage.py --input data/derived/submissions.json --output data/derived/metrics.json
python static_analysis.py --input data/derived/submissions.json --output data/derived/metrics.json
```

### 4. Statistical Analysis

```bash
cd code/analysis
python statistical_tests.py --input data/derived/metrics.json --output data/derived/analysis_results.json
python correction.py --input data/derived/analysis_results.json --output data/derived/corrected_results.json
python sensitivity.py --input data/derived/corrected_results.json --output data/derived/sensitivity_analysis.json
```

## Testing

```bash
# Contract tests (schema validation)
pytest tests/contract/ -v
 # - test_submission.py: validates Submission schema (FR-003, FR-012)
 # - test_metric.py: validates Metric schema (FR-004-007)
 # - test_analysis_result.py: validates Analysis Result schema (FR-008-011)

# Integration tests (end-to-end experiment)
pytest tests/integration/ -v

# Unit tests (quality metrics, statistical tests)
pytest tests/unit/ -v
```

## Reproducibility Check (Constitution I)

```bash
# Verify all random seeds are pinned
grep -r "random.seed" code/

# Verify dataset checksums
python code/data/checksums.py --verify

# Re-run full pipeline
make reproduce # Runs experiment → quality → analysis end-to-end
```

## Known Limitations

- **JaCoText Gap**: JaCoText has NO verified public source (research.md); may require spec change
- **Power Limitation**: 30 participants with 2 problems/condition may be underpowered for small effect sizes (d < 0.4)
- **Runtime Constraint**: 2 problems per condition to fit 6 h GitHub Actions job
- **Dropout Rate**: >20% dropout will reduce statistical power; incomplete data excluded
- **Construct Validity**: HumanEval/Codeforces are algorithmic benchmarks, not real development tasks