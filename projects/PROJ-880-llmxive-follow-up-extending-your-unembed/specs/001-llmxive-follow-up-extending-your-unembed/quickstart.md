# Quickstart: llmXive cross‑lingual edge‑spectrum analysis

## Environment Setup
```bash
# Create and activate environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install torch numpy scipy datasets scikit-learn jsonschema pytest
```

## Execution
The pipeline is executed via the orchestrator:
```bash
python -m src.pipeline.orchestrator \
    --models "llama3,mistral,bloom" \
    --languages "en,fr,zh,ar,sw,de,es,hi,ja,pt" \
    --top-k 100 \
    --perm-iterations 10000 \
    --seed 42
```

## Critical Guards
- **Data Guard**: If any language corpus contains $< 1,000,000$ tokens, the system raises `DataInsufficiencyError` and skips that language.
- **Time Guard**: If the permutation test exceeds 6 hours, the process aborts with a warning in `feasibility_report.json`.
- **Numerical Guard**: If $W_U$ is ill-conditioned ($> 10^8$), Tikhonov regularization ($\lambda=10^{-5}$) is automatically applied.

## Verification
Validate all derived artifacts against the contracts:
```bash
pytest tests/contract/
```
