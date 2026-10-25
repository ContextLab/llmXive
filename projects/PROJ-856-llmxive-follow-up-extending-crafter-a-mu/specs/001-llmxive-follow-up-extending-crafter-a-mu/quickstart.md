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
# Attempt to download a verified CrafterBench subset (50 failed figures)
python -m src.curators.curate_failed_figures \
    --download \
    --output-dir data/
```
- If a verified open‑source CrafterBench subset is **available**, the script will download and curate exactly 50 failed figures with injected errors and corresponding ground‑truth vectors.  
- If no verified source exists, the script aborts with an informative error; this signals that the required dataset must be provided before the study can proceed (FR‑001).  
- **Do not** rely on a synthetic surrogate for scientific conclusions; synthetic data is only used for CI‑verification of pipeline mechanics (see `simulate_participants.py`).

## 3. Run a priori power analysis
```bash
python -m src.simulation.power_analysis \
    --effect-size 0.5 \
    --alpha 0.025 \
    --test wilcoxon
```
*The script prints the required sample size (approximately a few dozen participants).*

## 4. Launch the interface stubs (sanity check)
```bash
# Structured harness on port 8001
uvicorn src.interfaces.structured_harness:app --port 8001 &
# Chat interface on port 8002
uvicorn src.interfaces.chat_interface:app --port 8002 &
sleep 2

# Verify session initialization (returns JSON with counterbalanced order and **10‑minute wash‑out interval**)
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
*These logs are **not** used for scientific conclusions; they only prove that the pipeline runs and conforms to schemas.*

## 6. Human‑Participant Data Collection (real study)
> Start the FastAPI servers (step 4) and recruit participants. The system will enforce randomization, counterbalancing, and a 10‑minute wash‑out interval between interface blocks. Collect NASA‑TLX scores after each task.

## 7. Retention check
```bash
python -m src.analysis.retention_check \
    --log-dir data/logs/ \
    --min-valid 28 \
    --required-participants 32
```

## 8. Validation (Vector match & Semantic similarity)
```bash
python -m src.validation.run_validation \
    --log-dir data/logs/ \
    --output-dir data/validation/
```

## 9. Statistical analysis and report generation
```bash
python -m src.analysis.wilcoxon_analysis \
    --log-dir data/logs/ \
    --validation-dir data/validation/ \
    --output-dir outputs/
python -m src.analysis.generate_report \
    --analysis-dir outputs/ \
    --output-file outputs/report.md
```

---

