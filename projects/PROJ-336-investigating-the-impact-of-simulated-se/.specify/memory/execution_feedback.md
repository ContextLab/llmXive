# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/data/preprocess.py --atlas schaefer400; python src/analysis/connectivity.py; python src/analysis/metrics.py; 2 command(s) failed: python code/src/data/download.py --dataset ds001770 (rc=1); python code/src/data/quality_check.py --fd_threshold 0.5 --volume_threshold 0.10 (rc=1)

## Failing / missing run-book commands

- python code/src/data/download.py --dataset ds001770 -> rc=1
(args, executable, preexec_fn, close_fds,
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/subprocess.py", line 1955, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: 'bids-dataset-download'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/code/src/data/download.py", line 276, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/code/src/data/download.py", line 269, in main
    path = download_dataset(dataset_id, output_dir)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/code/src/data/download.py", line 241, in download_dataset
    raise ValueError(
ValueError: Could not download ds001770. bids-dataset-download is not installed or failed. Please install it via: pip install bids-dataset-download or ensure the dataset is manually placed in {output_dir}.

- python src/data/preprocess.py --atlas schaefer400 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/data/preprocess.py': [Errno 2] No such file or directory

- python code/src/data/quality_check.py --fd_threshold 0.5 --volume_threshold 0.10 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/code/src/data/quality_check.py", line 277, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/code/src/data/quality_check.py", line 254, in main
    data_root = Path(config.RAW_DATA_DIR)
                     ^^^^^^^^^^^^^^^^^^^
AttributeError: module 'src.config' has no attribute 'RAW_DATA_DIR'

- python src/analysis/connectivity.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/analysis/connectivity.py': [Errno 2] No such file or directory

- python src/analysis/metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/analysis/metrics.py': [Errno 2] No such file or directory

- python src/analysis/stats.py --n_permutations 1000 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/analysis/stats.py': [Errno 2] No such file or directory

- python src/viz/plot_networks.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/viz/plot_networks.py': [Errno 2] No such file or directory

- python src/viz/plot_metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-336-investigating-the-impact-of-simulated-se/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-336-investigating-the-impact-of-simulated-se/src/viz/plot_metrics.py': [Errno 2] No such file or directory

