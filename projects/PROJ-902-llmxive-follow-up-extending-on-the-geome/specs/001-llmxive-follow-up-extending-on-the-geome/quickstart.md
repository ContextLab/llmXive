# Quickstart: llmXive follow-up – Geometry Extension

This guide walks a new researcher from a fresh clone to reproducing the full experimental matrix on a free GitHub Actions runner.

## Prerequisites
- GitHub account (to trigger CI).
- No local GPU required.

## Step‑by‑Step

1. **Clone the repository**
 ```bash
 git clone
 cd llmxive-geometry-extension
 ```

2. **Set up the Python environment**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Verify dataset download (optional local test)**
 ```bash
 python -m src.data.download_gsm8k
 # Should print "✅ GSM8K downloaded and checksum verified"
 ```

4. **Run a single seed locally (debug)**
 ```bash
 python -m src.cli.run_experiment \
 --condition frozen_opd \
 --seed 42 \
 --dry-run
 ```
 This executes the full pipeline for one seed and writes a temporary `state.yaml`.

5. **Trigger the full CI matrix**
 - Push a branch or open a PR; GitHub Actions will automatically start the workflow defined in `.github/workflows/ci.yml`.
 - The matrix contains five jobs (full_opd, frozen_opd, frozen_sft, random_sft, full_sft) each using the **TinyLlama‑430M** model and running **3 epochs**. Jobs run a set of seeds in parallel batches that respect the defined memory and time limits.

6. **Inspect results**
 - After CI succeeds, download the artifact `state.yaml` from the workflow summary.
 - Use the provided analysis script to generate figures:
 ```bash
 python -m src.analysis.generate_report --state results/state.yaml
 ```
 - The script produces `report.pdf` and a `figures/` directory.

7. **Re‑run with modified variance threshold (optional)**
 ```bash
 python -m src.cli.run_experiment \
 --condition frozen_opd \
 --variance-threshold 0.90 \
 --seed-list 1 2 3... 30
 ```

All random seeds are listed in `src/config/seeds.yaml`; they are pinned for reproducibility (Constitution Principle I).

---


