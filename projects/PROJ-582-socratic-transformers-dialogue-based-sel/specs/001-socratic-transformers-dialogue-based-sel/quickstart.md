# Quickstart: Socratic Transformers

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with 7GB+ RAM for testing)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd socratic-transformers
 ```

2. **Set up the virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt
 ```

## Running the Pipeline

### Step 1: Verify & Download Data
```bash
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/verify.py
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/download.py
```
*Note: This step downloads GSM8K and MATH datasets via streaming and records checksums.*

### Step 2: Generate Dialogue Tuples
```bash
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/generation/dialogue_gen.py --condition selection
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/generation/ablation_gen.py
```
*Note: This step includes the regeneration loop for quality control.*

### Step 3: Fine-tune Models
```bash
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/training/trainer.py --condition selection
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/training/trainer.py --condition ablation
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/training/trainer.py --condition static
```
*Note: Runs on CPU by default. If CUDA is available (Kaggle offload), it will automatically use it.*

### Step 4: Evaluate & Analyze
```bash
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/eval/runner.py
python projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/analysis/stats.py
```

## Validation

Run the contract tests to ensure data integrity:
```bash
pytest projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/contract/
```

## Troubleshooting

- **OOM Errors**: If you encounter memory errors on CPU, ensure `streaming=True` is used in data loading. The pipeline is designed to handle this, but local testing may require reducing batch sizes.
- **Dataset Access**: If HuggingFace downloads fail, verify your internet connection and ensure you are not behind a restrictive firewall.
