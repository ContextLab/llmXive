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
# Attempt to download the real CrafterBench subset (required for the human study)
python -m src.curators.curate_failed_figures \
    --num-tasks 50 \
    --output-dir data/
```
- If the verified URL (`https://huggingface.co/datasets/crafterbench`) cannot be reached, the script **exits with an informative error** and the pipeline halts (real study blocked).  
- To **only** verify the pipeline (CI), generate a deterministic synthetic surrogate:
```bash
python -m src.curators.curate_failed_figures \
    --verify-only \
    --num-tasks 50 \
    --output-dir data/
```
*These synthetic logs are **not** used for scientific conclusions; they only prove that the pipeline runs and conforms to schemas.*

## 3. Run a priori power analysis
```bash
python -m src.simulation.power_analysis \
    --effect-size 0.5 \
    --alpha 0.025 \   # Bonferroni‑adjusted significance level
    --test wilcoxon
```

## 4. Launch the interface stubs (manual sanity check)
```bash
# Structured harness on port 8001
uvicorn src.interfaces.structured_harness:app --port 8001 &
# Chat interface on port 8002
uvicorn src.interfaces.chat_interface:app --port 8002 &
sleep 2

# Verify session initialization (returns JSON with counterbalanced order and 2‑minute wash‑out interval)
curl -X POST http://127.0.0.1:8001/init_session -H "Content-Type: application/json" -d '{"participant_id":"test_user"}'
```

## 5. CI‑Only Pipeline Verification (synthetic participants)
```bash
python -m src.simulation.simulate_participants \
    --participants 30 \
    --seed 42 \
    --log-dir data/logs/
```
*These logs are **not** used for scientific conclusions; they only prove that the pipeline runs and conforms to schemas.*

## 6. Human‑Participant Data Collection (real study)
> Start the FastAPI servers (step 4) and have recruited participants interact with the interfaces. `interaction_logger.py` will automatically record real wall‑clock timestamps, iteration counts, and **NASA‑TLX** scores to `data/logs/`.

## 7. Retention check
```bash
python -m src.analysis.retention_check \
    --log-dir data/logs/ \
    --min-valid 25
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
python -m src.analysis.wilcoxon_analysis \
    --validation-dir data/validation/ \
    --output-dir outputs/
```

## 10. Verify contracts (CI gate)
```bash
pytest -q tests/contract
```

## 11. Run the full pipeline end‑to‑end
```bash
python -m src.run_pipeline --config config.yaml
```

---

