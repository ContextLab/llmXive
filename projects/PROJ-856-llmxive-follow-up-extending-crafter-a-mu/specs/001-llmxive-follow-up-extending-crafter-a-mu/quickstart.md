# Quickstart: llmXive follow-up – Cognitive Load Comparison Study

These commands assume a fresh GitHub Actions (or local) runner in the project root.

## 1. Set up the Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Dataset Curation
```bash
# Attempt to download the real CrafterBench subset (Required for research results)
python -m src.curators.curate_failed_figures \
    --num-tasks <appropriate count> \
    --output-dir data/
```
- **Note**: If no verified source is available, this script will fail. To test the software pipeline logic without real data, use the verification flag:
```bash
python -m src.curators.curate_failed_figures --verify-only --num-tasks 50 --output-dir data/
```
- After execution, check `data/figures/` and `data/ground_truth/`.

## 3. Run a priori power analysis
```bash
python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon
```

## 4. Launch the interface stubs (Manual Test)
```bash
uvicorn src.interfaces.structured_harness:app --port 8001 &
uvicorn src.interfaces.chat_interface:app --port 8002 &
sleep 2

# Verify session initialization (returns a successful HTTP status code and counterbalanced order)
curl -X POST Connection refused"))] -H "Content-Type: application/json" -d '{"participant_id":"test_user"}'
```

## 5. Software Pipeline Verification (CI-Only)
```bash
# Generates a large set of synthetic log entries to verify pipeline capacity and schema compliance.
# These logs are NOT used for research conclusions.
python -m src.simulation.simulate_participants \
    --participants a sufficient sample size \
    --seed 42 \
    --log-dir data/logs/
```

## 6. Human‑Participant Data Collection (Real Study)
> To conduct the actual research, start the FastAPI servers (Step 4) and have recruited participants interact with the interfaces. The `interaction_logger.py` will record real wall-clock timestamps to `data/logs/`.

## 7. Retention check
```bash
python -m src.analysis.retention_check --log-dir data/logs/ --min-valid 25
```

## 8. Validation (Vector + Semantic)
```bash
python -m src.validation.run_validation \
    --log-dir data/logs/ \
    --ground-truth-dir data/ground_truth/ \
    --output-dir data/validation/
```

## 9. Statistical analysis & report generation
```bash
python -m src.analysis.wilcoxon_analysis --validation-dir data/validation/ --output-dir outputs/
```

## 10. Verify contracts (CI gate)
```bash
pytest -q tests/contract
```

## 11. Run the full pipeline
```bash
python -m src.run_pipeline --config config.yaml
```
