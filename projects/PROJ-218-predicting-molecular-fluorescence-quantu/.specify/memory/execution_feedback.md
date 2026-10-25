# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50`
  - script usage: `scaffold_split.py [-h] [--input INPUT] [--output-dir OUTPUT_DIR]`
  - argparse error: `scaffold_split.py: error: unrecognized arguments: --min-test-size 50`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 command(s) failed: python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet (rc=1); python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet (rc=1); python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 (rc=2); 1 declared deliverable(s) absent: data/raw/fluordb/fluordb.parquet

## Failing / missing run-book commands

- python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet -> rc=1
pendency. No module named 'torch'
2026-10-25 00:12:39,204 WARNING deepchem.models: No module named 'torch'
2026-10-25 00:12:39,204 WARNING deepchem.models: Skipped loading modules with pytorch-geometric dependency, missing a dependency. No module named 'torch'
2026-10-25 00:12:39,204 WARNING deepchem.models: Skipped loading modules with pytorch-lightning dependency, missing a dependency. No module named 'torch'
2026-10-25 00:12:39,205 WARNING deepchem.models: Skipped loading some Jax models, missing a dependency. No module named 'jax'
2026-10-25 00:12:39,206 WARNING deepchem.metalearning: Skipped loading some PyTorch models, missing a dependency. No module named 'tensorflow'
2026-10-25 00:12:39,215 INFO deepchem.data.datasets: Loading dataset from disk.
2026-10-25 00:12:39,217 INFO deepchem.data.datasets: Loading dataset from disk.
2026-10-25 00:12:39,218 INFO deepchem.data.datasets: Loading dataset from disk.
2026-10-25 00:12:39,220 WARNING code.data.download_fluordb: DeepChem load failed (Per-column arrays must each be 1-dimensional); falling back to ESOL CSV.
2026-10-25 00:12:39,324 ERROR code.data.download_fluordb: Failed to load fallback CSV dataset: HTTP Error 404: Not Found

- python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet -> rc=1

2026-10-25 00:12:39,487 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:39,487 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:39,487 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: No module named src.preprocessing.clean

- python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 -> rc=2

2026-10-25 00:12:39,560 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:39,560 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:39,560 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
usage: scaffold_split.py [-h] [--input INPUT] [--output-dir OUTPUT_DIR]
scaffold_split.py: error: unrecognized arguments: --min-test-size 50

- python -m src.features.rdkit_features  --input data/processed/split/train.parquet  --output data/processed/features/train_graphs.pt -> rc=1

2026-10-25 00:12:39,823 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:39,823 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:39,824 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.rdkit_features' (ModuleNotFoundError: No module named 'src.features')

- python -m src.features.ecfp4  --input data/processed/split/train.parquet  --output data/processed/features/train_ecfp4.npy -> rc=1

2026-10-25 00:12:39,897 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:39,897 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:39,897 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.ecfp4' (ModuleNotFoundError: No module named 'src.features')

- python -m src.training.train  --graph-features data/processed/features/train_graphs.pt  --targets data/processed/split/train.parquet  --validation-split data/processed/split/validation.parquet  --epochs 50  --patience 10  --output models/gnn_best.pt -> rc=1

2026-10-25 00:12:39,977 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:39,978 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:39,978 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train' (ModuleNotFoundError: No module named 'src.training')

- python -m src.training.train_lr  --features data/processed/features/train_ecfp4.npy  --metadata data/processed/split/train.parquet  --output models/lr.pkl -> rc=1

2026-10-25 00:12:40,065 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,065 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,066 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train_lr' (ModuleNotFoundError: No module named 'src.training')

- python -m src.evaluation.evaluate  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --test-data data/processed/split/test.parquet  --output results/metrics.json  --fig-dir figures/ -> rc=1

2026-10-25 00:12:40,139 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,140 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,140 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.evaluate' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.interpretability.integrated_gradients  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --output attributions/ig/ -> rc=1

2026-10-25 00:12:40,212 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,213 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,213 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.integrated_gradients' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.shap_sanity  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --sample-size 100  --seeds 42 123 999  --output attributions/shap/ -> rc=1

2026-10-25 00:12:40,285 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,286 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,286 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.shap_sanity' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --output attributions/aggregated_top20.json -> rc=1

2026-10-25 00:12:40,357 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,358 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,358 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --atom-level  --output attributions/atom_top20.json -> rc=1

2026-10-25 00:12:40,429 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,430 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,430 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.validate_attributions  --aggregated attributions/aggregated_top20.json  --reference data/reference/fluorophore_motifs.csv  --train-data data/processed/split/train.parquet  --test-data data/processed/split/test.parquet  --output results/attribution_validation.json -> rc=1

2026-10-25 00:12:40,502 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,503 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,503 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.validate_attributions' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.evaluation.covariate_ablation  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --train-data data/processed/split/train.parquet  --validation-data data/processed/split/validation.parquet  --test-data data/processed/split/test.parquet  --output results/covariate_impact.json -> rc=1

2026-10-25 00:12:40,574 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,575 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,575 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.covariate_ablation' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.reporting.generate_report  --metrics results/metrics.json  --attribution-validation results/attribution_validation.json  --covariate-impact results/covariate_impact.json  --fig-dir figures/  --output report/ -> rc=1

2026-10-25 00:12:40,647 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-25 00:12:40,647 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-25 00:12:40,647 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.reporting.generate_report' (ModuleNotFoundError: No module named 'src.reporting')


## Declared deliverables still missing

- data/raw/fluordb/fluordb.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/fluordb/fluordb.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_fluordb.py` — NOT invoked by the run-book
    - `code/data/download_raw.py` — NOT invoked by the run-book
    - `src/data/download_fluordb.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/fluordb/fluordb.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
