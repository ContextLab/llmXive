# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 3 command(s) failed: python code/generate_data.py --seed 42 --overlap high (rc=1); python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning (rc=1); python -m pytest tests/contract/ (rc=2); 2 declared deliverable(s) absent: data/raw/skills.json; data/raw/tasks.json

## Failing / missing run-book commands

- python code/generate_data.py --seed 42 --overlap high -> rc=1
-MiniLM-L6-v2...
INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: all-MiniLM-L6-v2
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 283, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/generate_data.py", line 226, in main
    model = SentenceTransformer("all-MiniLM-L6-v2")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 87, in __init__
    snapshot_download(model_name_or_path,
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/util.py", line 491, in snapshot_download
    path = cached_download(**cached_download_args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cached_download() missing 2 required positional arguments: 'repo_id' and 'filename'

- python code/agent.py  --library-sizes 10 20 30 40 50 60 70 80 90 100  --overlap high  --pruning -> rc=1
b/python3.11/site-packages/sentence_transformers/__init__.py", line 3, in <module>
    from .datasets import SentencesDataset, ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py", line 3, in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py", line 4, in <module>
    from .. import SentenceTransformer
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 12, in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download
ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python code/analysis.py --input data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code/analysis.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=2
./.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py:3: in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
../../.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py:4: in <module>
    from .. import SentenceTransformer
../../.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py:12: in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download
E   ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/huggingface_hub/__init__.py)
=========================== short test summary info ============================
ERROR tests/contract/test_schemas.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 2.81s ===============================



## Declared deliverables still missing

- data/raw/skills.json
- data/raw/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/skills.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/skills.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/pruning.py` — NOT invoked by the run-book
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
