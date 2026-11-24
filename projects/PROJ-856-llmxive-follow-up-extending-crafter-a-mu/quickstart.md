# Quickstart: llmXive follow‑up – Cognitive Load Comparison Study

These commands assume you are inside the project root on a fresh GitHub Actions (or local) runner.

## 1. Set up the environment
```bash
# Create a fresh virtual environment (optional but recommended)
python -m venv.venv
source.venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## 2. Verify data availability
```bash
# Attempt to download the verified CrafterBench subset.
# This will abort with a clear error if the verified source is not reachable.
python -m src.curators.curate_failed_figures --output-dir data/
```
After execution you should see `data/figures/` and `data/ground_truth/` populated,
and a checksum file `data/checksums.txt` will be generated automatically.

## 3. Launch the interface stubs (optional interactive test)
```bash
# Structured harness on port 8001
uvicorn src.interfaces.structured_harness:app --port 8001 &

# Chat interface on port 8002
uvicorn src.interfaces.chat_interface:app --port 8002 &
```
You can verify that the services are running by visiting
` Connection refused"))] and ` Connection refused"))] (both should return a JSON
response with status `200`).

## 4. Run a priori power analysis (optional but recommended)
```bash
python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.025 --test wilcoxon
```
The script prints the minimum required participants (≈ 40 for the mixed‑effects model) and exits
with status 0 if the planned N meets or exceeds it.

## 5. Simulate participant sessions (CI‑friendly)
```bash
python -m src.simulation.simulate_participants \
 --participants 30 \
 --seed 42 \
 --log-dir data/logs/
```
This creates `data/logs/interactions_clean.jsonl` containing millisecond‑precise interaction records.

## 6. Retention check
```bash
python -m src.analysis.retention_check \
 --log-dir data/logs/ \
 --min-valid 28 \
 --required-participants 32
```
The command aborts the pipeline if fewer than the required number of participants have at least one
primary‑success trial.

## 7. Validation & analysis
```bash
# Validate each completed task (vector match + semantic similarity)
python -m src.validation.run_validation \
 --log-dir data/logs/ \
 --ground-truth-dir data/ground_truth/ \
 --output-dir data/validation/

# Perform statistical tests and generate the report
python -m src.analysis.wilcoxon_analysis \
 --validation-dir data/validation/ \
 --output-dir outputs/

python -m src.report.generate_report \
 --validation-dir data/validation/ \
 --output-file outputs/report.md
```

## 8. Inspect the final report
```bash
cat outputs/report.md
```
The report includes mean/median tables, test statistics, effect sizes, confidence intervals,
success‑rate breakdowns, and average NASA‑TLX scores.

## 9. Run contract tests (CI gate)
```bash
pytest -q tests/contract
```
All logs and the final analysis must pass the JSON‑schema contracts located in `contracts/`.

## 10. Run the end‑to‑end pipeline
```bash
python -m src.run_pipeline --config config.yaml
```
Expected output:
```
Pipeline completed
```

To view the installed version of the pipeline tooling:
```bash
python -m src.run_pipeline --version
```
This prints the semantic version string (e.g., `0.1.0`).
