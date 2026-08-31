# Quickstart: Running LlmXive in CI vs Research Mode

This guide provides the commands to run the LlmXive pipeline in either **CI Mode** (Simulation)
or **Research Mode** (Real Human Data).

## Prerequisites

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Ensure the project structure is initialized:
 ```bash
 python code/setup_project_structure.py
 ```

---

## Option A: CI Mode (Simulation)

Use this mode to validate the pipeline, test data flows, and benchmark latency without
needing real human annotations.

### 1. Set Mode
```bash
export MODE=CI
# Or in Python:
# python -c "from config import set_mode; set_mode('CI')"
```

### 2. Run Data Pipeline
Generates synthetic masks and decoupled scores.
```bash
python code/data/validate_and_log.py
```
**Expected Output**:
- `data/annotations/decoupled_scores.csv` (with `mode` column = `CI_MODE`)
- `data/results/validation_log.txt` (contains `[CI_MODE] Single-Rater Simulation`)

### 3. Run Proxy Validation
```bash
python code/eval/stats.py
```
**Expected Output**:
- `data/results/proxy_validation.json` with `gate_status: EXPECTED_LOW_CORRELATION`
- Pipeline continues (does not exit).

### 4. Run Evaluation (Ablation & Metrics)
```bash
python code/eval/ablation_runner.py
python code/eval/metrics.py
```
**Expected Output**:
- `data/results/ablation_report.json`
- `data/results/evaluation_report.json`

---

## Option B: Research Mode (Real Human Data)

Use this mode for scientific validation. **Requires** a real `human_scores.csv` file.

### 1. Prepare Data
Ensure `data/annotations/human_scores.csv` exists with columns:
`image_id`, `score`, `rater_id`.

### 2. Set Mode
```bash
export MODE=RESEARCH
```

### 3. Run Data Pipeline & Validation
```bash
python code/data/validate_and_log.py
```
**Expected Behavior**:
- Checks for `human_scores.csv`. If missing, **exits with code 1**.
- Calculates Krippendorff's alpha.
- Logs results to `data/results/validation_log.txt`.

### 4. Run Proxy Validation (The Gate)
```bash
python code/eval/stats.py
```
**Expected Behavior**:
- Calculates Pearson correlation between synthetic metrics and human scores.
- If $r < 0.7$: **Exits with code 1** (`gate_status: BLOCKED`).
- If $r \ge 0.7$: Proceeds (`gate_status: PASSED`).

### 5. Run Evaluation (Only if Gate Passed)
```bash
python code/eval/ablation_runner.py
python code/eval/metrics.py
```

---

## Troubleshooting

### "Missing human_scores.csv"
- **Cause**: Running in `RESEARCH` mode without the required file.
- **Fix**: Provide the file or switch to `MODE=CI`.

### "Proxy Validation Blocked"
- **Cause**: Correlation $r < 0.7$ in Research Mode.
- **Fix**: Review `data/results/proxy_validation.json`. This indicates the synthetic
 metrics do not predict human complexity well enough to justify training the gating head.
 Consider revising the mask generation strategy or collecting more diverse human data.

### "CI Mode: Low Correlation"
- **Cause**: Normal behavior in CI Mode.
- **Fix**: None. This confirms the decoupling logic is working.