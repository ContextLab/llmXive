# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python src/data/curate.py  --input data/raw/open_science_raw.jsonl  --output data/intermediate/open_sci_reason.jsonl  --filter ill_structured; python src/data/preprocess.py  --mmlu data/raw/mmlu_stem.jsonl  --opendsi data/intermediate/open_sci_reason.jsonl  --output data/intermediate/prompts_unified.jsonl; python src/inference/run_generation.py  --model SU-01  --dataset data/intermediate/prompts_unified.jsonl  --output data/intermediate/responses_SU01.jsonl  --temperature 0.7  --max_tokens 2048  --device cpu; 2 command(s) failed: python code/data/download.py --dataset HuggingFaceH4/mmlu --subset STEM --output data/raw/mmlu_stem.jsonl (rc=1); python code/data/download.py --dataset nvidia/OpenScience --output data/raw/open_science_raw.jsonl (rc=1)

## Failing / missing run-book commands

- python code/data/download.py --dataset HuggingFaceH4/mmlu --subset STEM --output data/raw/mmlu_stem.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/code/data/download.py", line 24, in <module>
    from datasets import load_dataset  # real HF datasets library
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/data/download.py --dataset nvidia/OpenScience --output data/raw/open_science_raw.jsonl -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/code/data/download.py", line 24, in <module>
    from datasets import load_dataset  # real HF datasets library
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/data/curate.py  --input data/raw/open_science_raw.jsonl  --output data/intermediate/open_sci_reason.jsonl  --filter ill_structured -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/data/curate.py': [Errno 2] No such file or directory

- python src/data/preprocess.py  --mmlu data/raw/mmlu_stem.jsonl  --opendsi data/intermediate/open_sci_reason.jsonl  --output data/intermediate/prompts_unified.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/data/preprocess.py': [Errno 2] No such file or directory

- python src/inference/run_generation.py  --model SU-01  --dataset data/intermediate/prompts_unified.jsonl  --output data/intermediate/responses_SU01.jsonl  --temperature 0.7  --max_tokens 2048  --device cpu -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/inference/run_generation.py': [Errno 2] No such file or directory

- python src/inference/scoring.py  --input data/intermediate/responses_SU01.jsonl  --model meta-llama/Meta-Llama-3-8B-Instruct  --output data/intermediate/scores.jsonl  --quantize 8bit -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/inference/scoring.py': [Errno 2] No such file or directory

- python src/analysis/validation.py  --scores data/intermediate/scores.jsonl  --gold-standard data/raw/gold_standard_50.json  --threshold 0.6  --fallback-mode auto -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/analysis/validation.py': [Errno 2] No such file or directory

- python src/analysis/simple_stats.py  --olympiad-scores data/intermediate/mmlu_results.jsonl  --open-sci-scores data/intermediate/scores.jsonl  --output data/final/simple_stats.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/analysis/simple_stats.py': [Errno 2] No such file or directory

- python src/analysis/lme_analysis.py  --data data/intermediate/scores.jsonl  --output data/final/lme_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-921-llmxive-follow-up-extending-achieving-go/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-921-llmxive-follow-up-extending-achieving-go/src/analysis/lme_analysis.py': [Errno 2] No such file or directory

