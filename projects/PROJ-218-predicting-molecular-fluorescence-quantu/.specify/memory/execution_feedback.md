# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 command(s) failed: python -m src.preprocessing.run  --smiles data/raw/smiles.parquet  --fqy data/raw/fqy.json  --output data/processed/dataset.csv  --split-output data/processed/split.json (rc=1); python -m src.training.train_gnn  --data data/processed/dataset.csv  --split data/processed/split.json  --epochs 50  --patience 10  --output models/gnn_best.pt (rc=1); python -m src.training.train_lr  --data data/processed/dataset.csv  --split data/processed/split.json  --output models/lr.pkl (rc=1)

## Failing / missing run-book commands

- python -m src.preprocessing.run  --smiles data/raw/smiles.parquet  --fqy data/raw/fqy.json  --output data/processed/dataset.csv  --split-output data/processed/split.json -> rc=1

2026-10-16 13:21:10,183 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:10,184 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: No module named src.preprocessing.run

- python -m src.training.train_gnn  --data data/processed/dataset.csv  --split data/processed/split.json  --epochs 50  --patience 10  --output models/gnn_best.pt -> rc=1

2026-10-16 13:21:11,295 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:11,296 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train_gnn' (ModuleNotFoundError: No module named 'src.training')

- python -m src.training.train_lr  --data data/processed/dataset.csv  --split data/processed/split.json  --output models/lr.pkl -> rc=1

2026-10-16 13:21:12,399 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:12,399 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.training.train_lr' (ModuleNotFoundError: No module named 'src.training')

- python -m src.evaluation.evaluate  --gnn-model models/gnn_best.pt  --lr-model models/lr.pkl  --data data/processed/dataset.csv  --split data/processed/split.json  --output results/metrics.json  --fig-dir figures/ -> rc=1

2026-10-16 13:21:13,485 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:13,485 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.evaluation.evaluate' (ModuleNotFoundError: No module named 'src.evaluation')

- python -m src.interpretability.compute_attributions  --model models/gnn_best.pt  --data data/processed/dataset.csv  --split data/processed/split.json  --top-k 20  --method integrated_gradients  --output attributions/ -> rc=1

2026-10-16 13:21:14,576 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:14,577 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.compute_attributions' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.interpretability.validate_attributions  --attribution-dir attributions/  --reference-motifs data/reference/fluorophore_motifs.csv  --output results/attribution_validation.json -> rc=1

2026-10-16 13:21:15,671 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:15,671 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.interpretability.validate_attributions' (ModuleNotFoundError: No module named 'src.interpretability')

- python -m src.reporting.generate_report  --metrics results/metrics.json  --attribution-validation results/attribution_validation.json  --fig-dir figures/  --output report/ -> rc=1

2026-10-16 13:21:16,777 INFO code.data.download_raw: Seeds initialized and recorded to /home/runner/work/llmXive/llmXive/projects/PROJ-218-predicting-molecular-fluorescence-quantu/results/seeds.json
2026-10-16 13:21:16,777 INFO utils.seed_assert: Seed assertion completed (checked PYTHONHASHSEED).
/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-218-predicting-molecular-fluorescence-quantu/bin/python: Error while finding module specification for 'src.reporting.generate_report' (ModuleNotFoundError: No module named 'src.reporting')

