# Quickstart: llmXive follow-up – Cognitive Load Comparison Study

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
# The script will attempt to download CrafterBench (via CIFAR-10); if unavailable it falls back to synthetic data.
python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/
```
- After execution you will see `data/figures/` and `data/ground_truth/`.
- A checksum file `data/checksums.txt` is generated automatically.

## 3. Launch the interface stubs (optional interactive test)
```bash
uvicorn src.interfaces.structured_harness:app --port 8001 &
uvicorn src.interfaces.chat_interface:app --port 8002 &
```
- Visit the endpoints (e.g., ` Connection refused"))]) to see a `200 OK` JSON response containing a randomized `interface_order` and shuffled `task_order`.

## 4. Run a priori power analysis (optional but recommended)
```bash
python -m src.simulation.power_analysis --effect-size 0.5 --alpha 0.05 --test wilcoxon
```
- The script prints the minimum required participants; abort if your planned N is lower.

## 5. Simulate participant sessions (CI‑friendly)
```bash
python -m src.simulation.simulate_participants \
 --participants 30 \
 --seed 42 \
 --log-dir data/logs/
```
- This creates `data/logs/interactions_clean.jsonl` containing millisecond‑precise interaction records.
- With 30 participants, 50 figures, and 5 edits per figure the file contains 7 500 lines, satisfying the contract schema. [UNRESOLVED-CLAIM: c_efc6dd26 — status=not_enough_info]

## 6. Retention check
```bash
python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25
```
- Fails the pipeline if fewer than 25 sessions have at least one non‑aborted successful trial.

## 7. Run validation & analysis
```bash
# Validate each completed task (vector OR semantic)
python -m src.validation.run_validation \
 --log-dir data/logs/ \
 --ground-truth-dir data/ground_truth/ \
 --output-dir data/validation/

# Perform statistical tests and generate the report
python -m src.analysis.wilcoxon_analysis \
 --validation-dir data/validation/ \
 --output-dir outputs/
```

## 8. Inspect the final report
```bash
cat outputs/report.md
```
The report includes:
- Median time‑to‑success & iteration counts per interface
- Wilcoxon signed‑rank statistic, Bonferroni‑adjusted p‑value, effect size
- Independent success‑rate breakdowns (vector‑match success, semantic‑similarity success)
- Notes on any aborted or corrupted tasks.

## 9. Run contract tests (CI gate)
```bash
pytest -q tests/contract
```
All logs and the final analysis must pass the JSON schema contracts located in `contracts/`.

## Run the end‑to‑end pipeline
The full study pipeline can be executed with a single command. It sequentially runs the data curation, simulation, validation, analysis, and report generation steps, respecting the deterministic configuration defined in `config.yaml`.

```bash
python -m src.run_pipeline --config config.yaml
```
Expected output:
```
Pipeline completed
```

The `src.run_pipeline` module seeds all randomness sources (Python `random`, NumPy, and PyTorch when available) to guarantee deterministic behaviour across runs.
