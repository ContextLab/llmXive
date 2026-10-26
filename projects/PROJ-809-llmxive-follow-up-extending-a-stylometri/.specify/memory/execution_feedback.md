# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python main.py; python main.py --phase ingestion; python main.py --phase training; 1 command(s) failed: python -m pytest tests/contract/ (rc=1)

## Failing / missing run-book commands

- python main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-809-llmxive-follow-up-extending-a-stylometri/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/main.py': [Errno 2] No such file or directory

- python main.py --phase ingestion -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-809-llmxive-follow-up-extending-a-stylometri/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/main.py': [Errno 2] No such file or directory

- python main.py --phase training -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-809-llmxive-follow-up-extending-a-stylometri/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/main.py': [Errno 2] No such file or directory

- python main.py --phase evaluation -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-809-llmxive-follow-up-extending-a-stylometri/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/main.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
09-llmxive-follow-up-extending-a-stylometri/artifacts/models')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/artifacts/models').exists

tests/contract/test_model_schema.py:42: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_model_schema.py::test_model_directory_exists - Ass...
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_manifest_exists
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_manifest_structure
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_author_directory_count
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_author_directory_naming
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_minimum_files_per_author
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_file_content_format
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_manifest_consistency
ERROR tests/contract/test_corpus_schema.py::TestCorpusSchema::test_no_unexpected_files
==================== 1 failed, 6 skipped, 8 errors in 0.17s ====================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
