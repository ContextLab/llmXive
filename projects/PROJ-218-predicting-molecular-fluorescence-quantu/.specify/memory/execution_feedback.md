# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 15 command(s) failed: python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet (rc=1); python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet (rc=1); python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 (rc=1); 1 declared deliverable(s) absent: data/raw/fluordb/fluordb.parquet

## Failing / missing run-book commands

- python -m src.data.download_fluordb  --url https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet  --output data/raw/fluordb.parquet -> rc=1
llib.request.urlopen(url) as response, open(dest_path, "wb") as out_file:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 216, in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 525, in open
    response = meth(req, response)
               ^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 634, in http_response
    response = self.parent.error(
               ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 563, in error
    return self._call_chain(*args)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 496, in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/urllib/request.py", line 643, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 404: Not Found

- python -m src.preprocessing.clean  --input data/raw/fluordb.parquet  --output data/processed/cleaned.parquet -> rc=1

2026-10-24 22:21:37,865 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:37,865 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:37,866 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: No module named src.preprocessing.clean

- python -m src.preprocessing.scaffold_split  --input data/processed/cleaned.parquet  --output-dir data/processed/split/  --min-test-size 50 -> rc=1

2026-10-24 22:21:37,992 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:37,993 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:37,993 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/src/preprocessing/scaffold_split.py", line 31, in <module>
    from rdkit import Chem
ModuleNotFoundError: No module named 'rdkit'

- python -m src.features.rdkit_features  --input data/processed/split/train.parquet  --output data/processed/features/train_graphs.pt -> rc=1

2026-10-24 22:21:38,367 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:38,368 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:38,368 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.rdkit_features' (ModuleNotFoundError: No module named 'src.features')

- python -m src.features.ecfp4  --input data/processed/split/train.parquet  --output data/processed/features/train_ecfp4.npy -> rc=1

2026-10-24 22:21:38,495 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:38,496 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:38,496 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.features.ecfp4' (ModuleNotFoundError: No module named 'src.features')

- python -m src.training.train  --graph-features data/processed/features/train_graphs.pt  --targets data/processed/split/train.parquet  --validation-split data/processed/split/validation.parquet  --epochs 50  --patience 10  --output models/gnn_best.pt -> rc=1

2026-10-24 22:21:38,621 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:38,622 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:38,622 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train' (ModuleNotFoundError: No module named 'src.training')

- python -m src.training.train_lr  --features data/processed/features/train_ecfp4.npy  --metadata data/processed/split/train.parquet  --output models/lr.pkl -> rc=1

2026-10-24 22:21:38,750 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:38,751 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:38,751 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train_lr' (ModuleNotFoundError: No module named 'src.training')

- python -m src.evaluation.evaluate  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --test-data data/processed/split/test.parquet  --output results/metrics.json  --fig-dir figures/ -> rc=1

2026-10-24 22:21:38,881 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:38,882 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:38,882 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.evaluate' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.interpretability.integrated_gradients  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --output attributions/ig/ -> rc=1

2026-10-24 22:21:39,016 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,017 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,017 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.integrated_gradients' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.shap_sanity  --model models/gnn_best.pt  --test-data data/processed/split/test.parquet  --sample-size 100  --seeds 42 123 999  --output attributions/shap/ -> rc=1

2026-10-24 22:21:39,152 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,153 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,153 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.shap_sanity' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --output attributions/aggregated_top20.json -> rc=1

2026-10-24 22:21:39,284 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,285 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,286 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.aggregate_substructures  --ig-dir attributions/ig/  --atom-level  --output attributions/atom_top20.json -> rc=1

2026-10-24 22:21:39,418 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,419 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,419 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.aggregate_substructures' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.validate_attributions  --aggregated attributions/aggregated_top20.json  --reference data/reference/fluorophore_motifs.csv  --train-data data/processed/split/train.parquet  --test-data data/processed/split/test.parquet  --output results/attribution_validation.json -> rc=1

2026-10-24 22:21:39,550 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,551 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,552 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.validate_attributions' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.evaluation.covariate_ablation  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --train-data data/processed/split/train.parquet  --validation-data data/processed/split/validation.parquet  --test-data data/processed/split/test.parquet  --output results/covariate_impact.json -> rc=1

2026-10-24 22:21:39,683 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,683 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,684 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.covariate_ablation' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.reporting.generate_report  --metrics results/metrics.json  --attribution-validation results/attribution_validation.json  --covariate-impact results/covariate_impact.json  --fig-dir figures/  --output report/ -> rc=1

2026-10-24 22:21:39,811 WARNING code.data.download_raw: torch not installed; skipping torch seed setting
2026-10-24 22:21:39,811 INFO code.data.download_raw: Wrote seed mapping to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-24 22:21:39,812 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
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
