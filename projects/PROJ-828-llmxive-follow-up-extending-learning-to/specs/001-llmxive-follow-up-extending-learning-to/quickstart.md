# Quickstart: Low-Rank RL for Foresight in LLM Training

## Prerequisites

- Python 3.10+
- Sufficient RAM (CPU-only execution)
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-828-llmxive-follow-up-extending-learning-to
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `torch` is installed for CPU only (e.g., `pip install torch --index-url https://download.pytorch.org/whl/cpu`).*

## Running the Experiment

**Important**: All experiments must be run via the `run_experiment.py` CLI. Do not run individual training scripts directly.

### 1. Data Preparation
Download and verify the GSM8K dataset:
```bash
python src/cli/run_experiment.py --prepare-data
```

### 2. Run the Full Pipeline
Execute the full experiment (OPD + Standard RL + Low-Rank RL + Random Projection + Random Walk + OPD-Initialized RL) with multiple seeds:
```bash
python src/cli/run_experiment.py --full-pipeline --seeds 10
```
*This command will:*
- Run OPD to generate the stable subspace.
- Train Standard RL, Low-Rank RL, Random Projection, Random Walk, and OPD-Initialized RL variants.
- Perform statistical analysis and power checks.
- Generate plots and logs.
- Compute and store artifact hashes in `state/` (satisfying Constitution Principle V).

### 3. Run a Single Variant (Optional)
To run only the Low-Rank RL variant (requires pre-computed OPD subspace):
```bash
python src/cli/run_experiment.py --variant low_rank_rl --seeds 10
```

### 4. Analyze Results
View the generated plots and metrics:
```bash
python src/cli/run_experiment.py --analyze
```
Or inspect the JSON summary:
```bash
cat results/analysis/alignment_metrics.json
```

## Verification

To verify the geometric constraint (Constitution Principle VI):
```bash
python src/cli/run_experiment.py --verify-alignment --variant low_rank_rl
```
*Expected output: "Alignment check passed: cosine similarity >= 0.99"*

## Troubleshooting

- **OOM Error**: If you encounter Out-Of-Memory errors, ensure `torch` is the CPU version and reduce `batch_size` in the config.
- **SVD Failure**: If SVD fails, the system will automatically default to `k=10` or use randomized SVD. Check logs for warnings.
- **Slow Execution**: The experiment is designed for a fixed duration. If it exceeds this, check if the dataset subset size is correct or if the number of seeds is too high (N=10 is the minimum for statistical power).
- **Hash Mismatch**: If the `state/` hash does not match `data/` checksums, re-run `--prepare-data` to ensure data integrity.