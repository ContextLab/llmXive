# Quickstart: llmXive follow‑up — Post‑generation Physics Filtering

Reproduce the full experiment on a fresh GitHub Actions free‑tier runner (or a Linux CPU box).

## Prerequisites

- Python 3.11, internet access, ~14 GB free disk.

## Steps

1. **Install & audit environment**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r code/requirements.txt
   python code/src/utils/verify_env.py
   ```
   `verify_env.py` asserts `torch.cuda.is_available() is False` (FR‑021) and validates `code/config.yaml` against `contracts/config.schema.yaml` (FR‑023).

2. **Download real Wan2.1 videos** (checksummed into `data/raw/`)
   ```bash
   python code/src/data/download_videos.py --config code/config.yaml
   ```
   This step streams the Rapidata parquet file and filters prompts for robotic‑manipulation keywords.

3. **Run the PyBullet physics filter and curate**
   ```bash
   python code/src/filtering/pybullet_filter.py --config code/config.yaml
   ```
   Scores each video (trajectory continuity + contact conservation; raw 0–100 → normalized 0–1), discards any video with normalized score < 0.60, writes curated and unfiltered manifests under `data/derived/manifests/`, and tops up with additional manipulation videos if n < 64 per condition.

4. **Validate contracts**
   ```bash
   pytest -q code/tests/contract/test_contracts.py
   ```

5. **Train the ≈ 50 M‑parameter distilled diffusion model** (both conditions)
   ```bash
   python code/src/training/train_diffusion.py --config code/config.yaml --condition filtered
   python code/src/training/train_diffusion.py --config code/config.yaml --condition unfiltered
   ```
   CPU‑only, pinned seed, NaN‑loss guard (≤ 3 LR retries), monotonic‑loss check, ≤ 4 h; duration and peak RAM recorded (SC‑005).

6. **Generate videos from each trained model**
   ```bash
   python code/src/evaluation/generate_videos.py --config code/config.yaml --model filtered
   python code/src/evaluation/generate_videos.py --config code/config.yaml --model unfiltered
   ```
   Produces ≥ 64 new videos per model into `data/derived/generated/`.

7. **MuJoCo independent validation**
   ```bash
   python code/src/filtering/mujoco_validator.py --config code/config.yaml
   ```
   Produces MuJoCo physics‑consistency scores and the PyBullet–MuJoCo correlation (SC‑006).

8. **Check go/no‑go sanity gate**
   ```bash
   # Exits with a non-zero code if the pass rate is < 80%
   python code/src/evaluation/check_gate.py --config code/config.yaml
   ```
   If the gate fails, the pipeline stops and logs a null‑result record (T12–T14 are skipped); otherwise continue.

9. **Evaluate benchmarks**
   ```bash
   python code/src/evaluation/evaluate_benchmarks.py --config code/config.yaml
   ```
   R‑Bench and PAI‑Bench scores for the filtered model, unfiltered baseline, and PhysisForcing baseline; computes the % gap (SC‑002, SC‑003).

10. **TOST equivalence test**
    ```bash
    python code/src/evaluation/tost_equivalence.py --config code/config.yaml
    ```
    Shapiro‑Wilk / Levene / independence diagnostics; primary TOST (filtered vs. unfiltered) with 15 % margin, α = 0.05; Mann‑Whitney fallback on assumption violation (SC‑004).

11. **Final report**
    ```bash
    python code/src/evaluation/generate_report.py --config code/config.yaml
    ```
    `data/reports/final_summary.md` aggregates SC‑001–SC‑006, all values read from the JSON/CSV artifacts.

The CI workflow runs the full sequence of steps (FR‑022), guaranteeing end‑to‑end reproducibility from a clean runner.