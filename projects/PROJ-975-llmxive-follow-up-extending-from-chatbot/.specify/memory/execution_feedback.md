# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 3 command(s) failed: python code/generate_data.py --seed 42 --overlap high (rc=1); python code/agent.py  --library-sizes 10 30 50 100  --pruning  --overlap high (rc=1); python -m pytest tests/contract/ (rc=1); 2 declared deliverable(s) absent: data/raw/skills.json; data/raw/tasks.json

## Failing / missing run-book commands

- python code/generate_data.py --seed 42 --overlap high -> rc=1
b/python3.11/site-packages/sentence_transformers/__init__.py", line 3, in <module>
    from .datasets import SentencesDataset, ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py", line 3, in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py", line 4, in <module>
    from .. import SentenceTransformer
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 12, in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download
ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-975-llmxive-follow-up-extending-from-chatbot/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python code/agent.py  --library-sizes 10 30 50 100  --pruning  --overlap high -> rc=1
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

- python -m pytest tests/contract/ -> rc=1
"task_id": "TASK_SAMPLE_001",
            "description": "Calculate the sum of two numbers and return the result.",
            "ground_truth_path": ["skill_add", "skill_return"],
            "complexity": 2
        }
        try:
            validate(instance=sample_task, schema=schema)
        except ValidationError as e:
>           pytest.fail(f"Sample task failed schema validation: {e.message}")
E           Failed: Sample task failed schema validation: 'embedding_vector' is a required property

tests/contract/test_task_schema.py:48: Failed
=========================== short test summary info ============================
FAILED tests/contract/test_skill_schema.py::test_schema_loads - Failed: Schem...
FAILED tests/contract/test_skill_schema.py::test_valid_skill_object - Failed:...
FAILED tests/contract/test_skill_schema.py::test_missing_required_field - Fai...
FAILED tests/contract/test_skill_schema.py::test_wrong_type_field - Failed: S...
FAILED tests/contract/test_skill_schema.py::test_negative_usage_count - Faile...
FAILED tests/contract/test_task_schema.py::test_sample_task_validates - Faile...
=================== 6 failed, 18 passed, 3 skipped in 0.20s ====================



## Declared deliverables still missing

- data/raw/skills.json
- data/raw/tasks.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/skills.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/skills.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/tasks.json` is declared but was NOT written. Scripts referencing it:
    - `code/agent.py` — IS a run-book command
    - `code/generate_data.py` — IS a run-book command
    - `code/run_baseline.py` — NOT invoked by the run-book
    - `code/run_experiment.py` — NOT invoked by the run-book
    - `code/run_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/tasks.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
