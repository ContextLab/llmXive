# Quickstart: Domino Mechanism Verification

This guide runs the scaled-down adaptation of the **Domino** paper. It verifies the core claim: that a lightweight causal refinement head (Domino) improves draft quality over a parallel draft backbone, using tiny models on a CPU.

## Prerequisites
- Python 3.9+
- `pip install torch transformers datasets numpy`

## Run Commands
Execute the following command to run the verification:

```bash
python code/verify_domino_mechanism.py
```

## Expected Output
The script will:
1. Load tiny GPT-2 models (Target) and DistilGPT-2 (Draft).
2. Process the first 50 samples of the GSM8K dataset.
3. Simulate speculative decoding steps.
4. Calculate **Acceptance Rates** and **KL Divergence** for:
   - Baseline (Parallel Draft)
   - Domino (Refined Draft)
5. Save results to `data/results.json` and `data/results.csv`.

## Verification
Check `data/results.json` for the `acceptance_improvement_pct`. A positive value confirms the Domino mechanism improves draft quality, aligning with the paper's core quantitative claim.
