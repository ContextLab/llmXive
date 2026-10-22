# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python code/generate_llm_variants.py  --model codellama-7b-instruct  --input data/raw/codeforces_cpp.jsonl  --output data/generated/codellama/; python code/generate_llm_variants.py  --model starcoder-15b  --input data/raw/codeforces_cpp.jsonl  --output data/generated/starcoder/; python code/create_problem_pairs.py  --human data/raw/codeforces_cpp.jsonl  --llm-dir data/generated/  --output data/raw/problem_pairs_v${HASH}.jsonl; 2 command(s) failed: python code/download_human.py  --output data/raw/codeforces_cpp.jsonl  --min-problems 50  --seed 20231027 (rc=1); python -m pytest -m contract (rc=5)

## Failing / missing run-book commands

- python code/download_human.py  --output data/raw/codeforces_cpp.jsonl  --min-problems 50  --seed 20231027 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/download_human.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/__init__.py", line 18, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/generate_llm_variants.py  --model codellama-7b-instruct  --input data/raw/codeforces_cpp.jsonl  --output data/generated/codellama/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_llm_variants.py': [Errno 2] No such file or directory

- python code/generate_llm_variants.py  --model starcoder-15b  --input data/raw/codeforces_cpp.jsonl  --output data/generated/starcoder/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_llm_variants.py': [Errno 2] No such file or directory

- python code/create_problem_pairs.py  --human data/raw/codeforces_cpp.jsonl  --llm-dir data/generated/  --output data/raw/problem_pairs_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/create_problem_pairs.py': [Errno 2] No such file or directory

- python code/compile_and_fuzz.py  --pairs data/raw/problem_pairs_v*.jsonl  --output data/results/fuzz_results_v${HASH}.jsonl  --timeout 1800   # 30 min per binary -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/compile_and_fuzz.py': [Errno 2] No such file or directory

- python code/parse_crashes.py  --fuzz-results data/results/fuzz_results_v${HASH}.jsonl  --output data/results/scored_fuzz_results_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/parse_crashes.py': [Errno 2] No such file or directory

- python code/statistical_analysis.py  --results data/results/scored_fuzz_results_v${HASH}.jsonl  --output data/analysis/stat_summary_v${HASH}.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/statistical_analysis.py': [Errno 2] No such file or directory

- python code/generate_report.py  --summary data/analysis/stat_summary_v${HASH}.jsonl  --output report.md -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-157-evaluating-the-impact-of-code-generation/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-157-evaluating-the-impact-of-code-generation/code/generate_report.py': [Errno 2] No such file or directory

- python -m pytest -m contract -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
collected 1 item / 1 deselected / 0 selected

============================ 1 deselected in 0.12s =============================


