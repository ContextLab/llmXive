# Quickstart: llmXive follow-up: extending "Qwen-Image-Flash: Beyond Objective Design"

## Prerequisites

* Python 3.11+
* Git
* A GitHub Actions free‑tier runner (or local machine with 7 GB+ RAM, 2 + CPU cores).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-845-llmxive-follow-up-extending-qwen-image-f
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `torch` is installed with CPU support only (e.g., `pip install torch --index-url https://download.pytorch.org/whl/cpu`).*

## Running the Pipeline

The entire pipeline (Generation → Validation → Distillation → Evaluation → Analysis → Report) is orchestrated by `code/main.py`.

### Step 1: Generate Synthetic Data
```bash
python code/main.py --phase generate --output data/raw/
```
*Creates `high_entropy.csv`, `low_entropy.csv`, `target_specific.csv`, and `test_set.csv` (the balanced Generalization Set).*

### Step 2: Validate Entropy
```bash
python code/main.py --phase validate_entropy --input data/raw/
```
*Confirms a statistically significant entropy gap between High and Low subsets.*

### Step 3: Generate Teacher Traces
```bash
python code/main.py --phase teacher_traces --input data/raw/ --output data/raw/
```
*Produces 10‑step CoT traces for every training problem.*

### Step 4: Validate Trace Consistency
```bash
python code/main.py --phase validate_traces --input data/raw/
```
*Computes trace entropy and filters out any problem where `trace_consistent` is false (FR‑009).*

### Step 5: Validate Generalization Set Structure
```bash
python code/main.py --phase validate_generalization --input data/raw/
```
*Verifies that the Generalization Set is structurally distinct from training data and stratified by structure type.*

### Step 6: Distillation (3 runs)
```bash
python code/main.py --phase distill --input data/raw/ --output data/processed/
```
*Runs three distillation sessions (High, Low, Target). The three `DistillationRun` records map directly to the three entropy subsets (see plan).*

### Step 7: Evaluation
```bash
python code/main.py --phase evaluate --input data/processed/ --output data/processed/
```
*Evaluates each student on the Generalization Set and records accuracy & convergence epoch.*

### Step 8: Statistical Analysis
```bash
python code/main.py --phase analyze --input data/processed/ --output data/processed/stats.json
```
*Runs ANOVA and pairwise t‑tests, applying Bonferroni correction to **all** p‑values.*

### Step 9: Report Generation
```bash
python code/main.py --phase report --input data/processed/stats.json --output report.txt
```
*Creates a human‑readable summary that explicitly frames the findings as causal within the synthetic domain (FR‑006).*

## Troubleshooting

* **CUDA Error**: If you see "CUDA out of memory", verify you installed the CPU‑only PyTorch wheel.  
* **Timeout**: If the pipeline exceeds 6 h, it exits with code 1; check `data/processed/runs.jsonl` for `status: failed_timeout`.  
* **Non‑Convergence**: If a run logs `status: failed_non_converge`, the epoch is recorded as the maximum allowed and included in the statistical analysis as a worst‑case value.