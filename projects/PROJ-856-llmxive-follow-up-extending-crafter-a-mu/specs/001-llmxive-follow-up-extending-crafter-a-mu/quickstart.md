# Quickstart: llmXive follow‑up – Cognitive Load Comparison Study

These commands assume a fresh GitHub Actions (or local) runner in the project root.

## 1. Set up the Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Dataset Curation
```bash
# Attempt to download a verified CrafterBench subset (several failed figures)
python -m src.curators.curate_failed_figures \
    --download \
    --output-dir data/
```
- If a **verified** open‑source CrafterBench subset is **available**, the script will download and curate a representative set of failed figures with injected errors and corresponding ground‑truth vectors.  
- If no verified source exists, the script aborts with an informative error; this signals that the required dataset must be provided before the study can proceed (FR‑001).  
- **Do not** rely on a synthetic surrogate for scientific conclusions; synthetic data is only used for CI‑verification of pipeline mechanics (see `simulate_participants.py`).

## 3. Run a priori power analysis
```bash
python -m src.simulation.power_analysis \
    --effect-size 0.5 \
    --alpha 0.025 \
    --test mixed_effects
```
*The script prints the required sample size (a sufficient number of participants for the mixed‑effects model with expertise covariate) and exits with status 0 if the planned N meets or exceeds it.*

## 4. Launch the interface stubs (sanity check)
```bash
# Structured harness on port 8001
uvicorn src.interfaces.structured_harness:app --port 8001 &
# Chat interface on port 8002
uvicorn src.interfaces.chat_interface:app --port 8002 &
sleep 2

# Verify session initialization (returns JSON with counterbalanced order **and** **5‑minute** wash‑out)
curl -X POST Connection refused"))] \
    -H "Content-Type: application/json" \
    -d '{"participant_id":"test_user"}'
```

## 5. CI‑Only Pipeline Verification (synthetic participants)
```bash
python -m src.simulation.simulate_participants \
    --participants 30 \
    --seed 42 \
    --log-dir data/logs/
```
*These logs ​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​```


