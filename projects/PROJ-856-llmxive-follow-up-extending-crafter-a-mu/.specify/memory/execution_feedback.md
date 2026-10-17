# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ (rc=1); python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 (rc=1); python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ (rc=1)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/ -> rc=1
ine 218, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/curators/curate_failed_figures.py", line 215, in main
    curate_failed_figures(num=args.num, output_dir=args.output_dir)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/curators/curate_failed_figures.py", line 163, in curate_failed_figures
    samples = _load_crafterbench(num)
              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/src/curators/curate_failed_figures.py", line 88, in _load_crafterbench
    dataset = CIFAR10(root=str(cache_dir), train=True, download=False)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/lib/python3.11/site-packages/torchvision/datasets/cifar.py", line 69, in __init__
    raise RuntimeError("Dataset not found or corrupted. You can use download=True to download it")
RuntimeError: Dataset not found or corrupted. You can use download=True to download it

- python -m src.utils.check_retention --log-dir data/logs/ --min-valid 25 -> rc=1

Error processing validation file: "Successful validation record missing session identifier: {'figure_id': '0', 'vector_match': True, 'semantic_pass': True, 'similarity_score': 1.0}"

- python -m src.analysis.wilcoxon_analysis  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

2026-10-17 04:10:50,137 ERROR __main__: Validation records missing required columns: {'time_to_success_ms', 'participant_id', 'interface', 'iteration_count'}

- python -m pytest -q tests/contract -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract


