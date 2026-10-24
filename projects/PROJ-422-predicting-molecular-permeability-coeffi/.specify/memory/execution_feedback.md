# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash ./run_all.sh; 2 command(s) failed: python code/analysis/train.py --config config.yaml (rc=1); python code/analysis/explain.py (rc=1)

## Failing / missing run-book commands

- python code/analysis/train.py --config config.yaml -> rc=1
RROR", "task_id": "T004", "logger": "root", "message": "Traceback (most recent call last):\n  File \"/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py\", line 342, in main\n    _, feature_cols, X_train, y_train = load_data(train_path, target_col=\"target\")\n                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"/home/runner/work/llmXive/llmXive/projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis/train.py\", line 79, in load_data\n    X = df[feature_cols].values.astype(np.float32)\n        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nValueError: could not convert string to float: '[{\"atom_idx\": 0, \"symbol\": \"C\", \"atomic_num\": 6, \"degree\": 1, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}, {\"atom_idx\": 1, \"symbol\": \"C\", \"atomic_num\": 6, \"degree\": 2, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}, {\"atom_idx\": 2, \"symbol\": \"O\", \"atomic_num\": 8, \"degree\": 1, \"formal_charge\": 0, \"hybridization\": \"SP3\", \"aromatic\": false}]'\n", "module": "train", "function": "main", "line": 473}


- python code/analysis/explain.py -> rc=1
{"timestamp": "2026-10-24T21:18:25.347827+00:00", "level": "ERROR", "task_id": "T004", "logger": "__main__", "message": "Model checkpoint not found at data/interim/gnn_checkpoint.pt. Please run training (T022) first.", "module": "explain", "function": "main", "line": 229}

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-422-predicting-molecular-permeability-coeffi/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
  warnings.warn(

- bash ./run_all.sh -> rc=-1

shell script must be an existing project-local .sh file
