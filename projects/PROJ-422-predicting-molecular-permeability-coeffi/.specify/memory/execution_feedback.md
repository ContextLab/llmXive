# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/processed/split_metadata.json: metric is null/NaN (max_distribution_diff) — not a real measurement

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/processed/split_metadata.json: metric is null/NaN (max_distribution_diff) — not a real measurement; 2 command(s) failed: python code/analysis/explain.py (rc=1); bash ./run_all.sh (rc=1)

## Failing / missing run-book commands

- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-26T07:57:56.712752+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=1
training complete. Feature importances shape: (6,)
2026-10-26 07:58:04,363 INFO __main__: Random Forest model saved to code/models/rf.pkl
2026-10-26 07:58:04,364 INFO __main__: Training log written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/results/training_log.json
2026-10-26 07:58:04,364 INFO __main__: Hand‑off document written to /home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/results/results.md
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/evaluate.py", line 13, in <module>
    from models.gnn import create_mpnn_model, validate_epoch
ImportError: cannot import name 'validate_epoch' from 'models.gnn' (/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models/gnn.py)

