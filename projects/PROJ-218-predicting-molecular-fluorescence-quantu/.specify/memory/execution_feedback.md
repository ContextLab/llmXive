# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 command(s) failed: python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet (rc=1); python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet (rc=1); python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 (rc=1); 1 declared deliverable(s) absent: data/raw/fluordb/fluordb.parquet

## Failing / missing run-book commands

- python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet -> rc=1

2026-10-24 21:23:14,572 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:14,573 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:14,573 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
2026-10-24 21:23:15,119 INFO httpx2: HTTP Request: GET https://huggingface.co/api/datasets/fluordb/v1 "HTTP/1.1 401 Unauthorized"
2026-10-24 21:23:15,120 ERROR code.data.download_fluordb: Failed to load FluorDB via datasets: Dataset 'fluordb/v1' doesn't exist on the Hub or cannot be accessed.

- python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet -> rc=1

2026-10-24 21:23:15,333 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,334 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,334 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: No module named src.preprocessing.clean

- python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 -> rc=1

2026-10-24 21:23:15,416 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,416 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,416 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/preprocessing/scaffold_split.py", line 31, in <module>
    from rdkit import Chem
ModuleNotFoundError: No module named 'rdkit'

- python -m src.features.rdkit_features  --input data/processed/split/train.parquet  --output data/processed/features/train_graphs.pt -> rc=1

2026-10-24 21:23:15,679 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,679 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,679 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.rdkit_features' (ModuleNotFoundError: No module named 'src.features')

- python -m src.features.ecfp4  --input data/processed/split/train.parquet  --output data/processed/features/train_ecfp4.npy -> rc=1

2026-10-24 21:23:15,754 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,757 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,757 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.ecfp4' (ModuleNotFoundError: No module named 'src.features')

- python -m src.training.train  --graph-features data/processed/features/train_graphs.pt  --targets data/processed/split/train.parquet  --validation-split data/processed/split/validation.parquet  --epochs 50  --patience 10  --output models/gnn_best.pt -> rc=1

2026-10-24 21:23:15,834 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,835 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,835 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train' (ModuleNotFoundError: No module named 'src.training')

- python -m src.training.train_lr  --features data/processed/features/train_ecfp4.npy  --metadata data/processed/split/train.parquet  --output models/lr.pkl -> rc=1

2026-10-24 21:23:15,913 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,914 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,914 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train_lr' (ModuleNotFoundError: No module named 'src.training')

- python -m src.evaluation.evaluate  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --test-data data/processed/split/test.parquet  --output results/metrics.json  --fig-dir figures/ -> rc=1

2026-10-24 21:23:15,993 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:15,994 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:15,994 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.evaluate' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.interpretability.integrated_gradients  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --output attributions/ig/ -> rc=1

2026-10-24 21:23:16,073 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,074 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,074 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.integrated_gradients' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.shap_sanity  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --sample-size 100  --seeds 42 123 999  --output attributions/shap/ -> rc=1

2026-10-24 21:23:16,152 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,153 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,153 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.shap_sanity' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --output attributions/aggregated_top20.json -> rc=1

2026-10-24 21:23:16,231 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,231 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,232 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --atom-level  --output attributions/atom_top20.json -> rc=1

2026-10-24 21:23:16,312 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,313 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,313 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.validate_attributions  --aggregated attributions/aggregated_top20.json  --reference data/reference/fluorophore_motifs.csv  --train-data data/processed/split/train.parquet  --test-data data/processed/split/test.parquet  --output results/attribution_validation.json -> rc=1

2026-10-24 21:23:16,394 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,395 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,395 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.validate_attributions' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.evaluation.covariate_ablation  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --train-data data/processed/split/train.parquet  --validation-data data/processed/split/validation.parquet  --test-data data/processed/split/test.parquet  --output results/covariate_impact.json -> rc=1

2026-10-24 21:23:16,476 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,477 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,477 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.covariate_ablation' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.reporting.generate_report  --metrics results/metrics.json  --attribution-validation results/attribution_validation.json  --covariate-impact results/covariate_impact.json  --fig-dir figures/  --output report/ -> rc=1

2026-10-24 21:23:16,557 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 21:23:16,558 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 21:23:16,558 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
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
