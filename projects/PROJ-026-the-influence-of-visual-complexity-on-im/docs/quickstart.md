# Quick Start Guide

Get up and running with the Visual Complexity pipeline in minutes.

## Step 1: Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd <project-dir>

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
cd code
pip install -r requirements.txt
```

## Step 2: Data Preparation

### Option A: Real Data
Place your image files in `data/raw/stimuli/` and response logs in `data/raw/responses/`.

### Option B: Synthetic Data (CI/Testing)
No data preparation needed. Use the `--null-effect` flag.

## Step 3: Run the Pipeline

```bash
cd code
python main.py
```

**Expected Output:**
- `data/processed/complexity_scores.csv`
- `data/processed/aggregated_d_scores.csv`
- `data/results/permutation_results.json`
- `figures/` (plots)

## Step 4: Verify Results

Check the `data/results/permutation_results.json` file for the p-value and effect size.

```json
{
 "p_value": 0.032,
 "effect_size": 0.45,
 "n_permutations": 10000,
 "status": "significant"
}
```

## Step 5: Troubleshooting

- **Error: "No images found"**: Ensure images are in `data/raw/stimuli/`.
- **Error: "Permission denied"**: Check file permissions or run as the correct user.
- **Slow Performance**: Ensure you are not running other heavy processes; the pipeline is CPU-bound.

## Next Steps

- Read `docs/usage_examples.md` for advanced usage.
- Review `docs/research.md` for methodological details.
- Check `docs/api_reference.md` for developer documentation.