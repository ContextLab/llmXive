# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess.py: function `apply_schaefer_parcellation` returns a bare RNG draw (line 85) — a reported value computed from no real input
- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…RITICAL: Do NOT generate fake data. Fail loudly if real dat…”
- code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ipeline does not support simulated neuroimaging data."             )…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess.py: function `apply_schaefer_parcellation` returns a bare RNG draw (line 85) — a reported value computed from no real input; code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…RITICAL: Do NOT generate fake data. Fail loudly if real dat…”; code/data/download_hcp.py: synthetic/fake INPUT data not authorized by the spec — “…ipeline does not support simulated neuroimaging data."             )…”; 2 command(s) failed: python code/data/download_hcp.py (rc=1); python code/main.py (rc=1); 1 declared deliverable(s) absent: data/processed/predictions.npy

## Failing / missing run-book commands

- python code/data/download_hcp.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/download_hcp.py", line 246, in <module>
    sys.exit(0 if main() else 1)
                  ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/data/download_hcp.py", line 212, in main
    behavioral_path = paths['raw_dir'] / "behavioral" / "hcp1200_behavioral_data.csv"
                      ~~~~~^^^^^^^^^^^
KeyError: 'raw_dir'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/main.py", line 23, in <module>
    from modeling.train import main as train_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/modeling/__init__.py", line 6, in <module>
    from .train import load_data, run_training, main as train_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/modeling/train.py", line 16, in <module>
    from utils.metrics import pearson_r, r_squared
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-736-predicting-personal-sleep-quality-from-r/code/utils/metrics.py", line 51, in <module>
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
                                                                     ^^^^
NameError: name 'Dict' is not defined. Did you mean: 'dict'?

## Declared deliverables still missing

- data/processed/predictions.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/predictions.npy` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/modeling/__init__.py` — NOT invoked by the run-book
    - `code/modeling/evaluate.py` — NOT invoked by the run-book
    - `code/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/predictions.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `hcp1200_behavioral_data.csv`

- ACTUAL columns/keys the producer wrote: `(file not on disk this run)`
- REQUIRED by the consumer(s): `[raw_dir]`
- PRODUCER(s) to edit: `code/data/download_hcp.py`
- CONSUMER(s) that read it: `code/config.py`, `code/main.py`, `code/data/download_hcp.py`, `code/data/preprocess.py`
  → Edit the producer so every required name [raw_dir] is in `hcp1200_behavioral_data.csv`'s header (renaming, not dropping, the columns it already writes); do not change the consumers (they already agree).
