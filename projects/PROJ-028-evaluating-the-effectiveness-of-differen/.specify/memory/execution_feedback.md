# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.cli.main  --strategy zero-shot  --seeds 3  --max-tasks 50  --output-dir data/results/baseline (rc=1); python -m src.cli.main  --strategies zero-shot few-shot cot  --seeds 3  --max-tasks 500  --k-samples 10  --output-dir data/results/full_run (rc=1); python -m src.analysis.stats  --input-dir data/results/full_run  --output data/reports/final_report.json (rc=1)

## Failing / missing run-book commands

- python -m src.cli.main  --strategy zero-shot  --seeds 3  --max-tasks 50  --output-dir data/results/baseline -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-028-evaluating-the-effectiveness-of-differen/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')

- python -m src.cli.main  --strategies zero-shot few-shot cot  --seeds 3  --max-tasks 500  --k-samples 10  --output-dir data/results/full_run -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-028-evaluating-the-effectiveness-of-differen/bin/python: Error while finding module specification for 'src.cli.main' (ModuleNotFoundError: No module named 'src.cli')

- python -m src.analysis.stats  --input-dir data/results/full_run  --output data/reports/final_report.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-028-evaluating-the-effectiveness-of-differen/bin/python: Error while finding module specification for 'src.analysis.stats' (ModuleNotFoundError: No module named 'src.analysis')

- python -m pytest tests/unit/ -v -> rc=1
.py::TestFewShotPromptStructure::test_prompt_structure_order
FAILED tests/unit/test_fewshot_prompt.py::TestFewShotPromptStructure::test_prompt_with_empty_examples
FAILED tests/unit/test_fewshot_prompt.py::TestFewShotPromptStructure::test_prompt_contains_generation_instruction
FAILED tests/unit/test_fewshot_prompt.py::TestFewShotPromptStructure::test_format_examples_function
FAILED tests/unit/test_fewshot_prompt.py::TestFewShotPromptStructure::test_few_shot_prompt_example_count
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_extract_single_python_block
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_extract_generic_markdown_block
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_extract_multiple_blocks
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_extract_with_trailing_whitespace
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_case_insensitivity
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_complex_code_content
FAILED tests/unit/test_prompt_parser.py::TestPromptParser::test_code_with_fenced_content_inside
========================= 14 failed, 4 passed in 0.13s =========================


- python -m pytest tests/integration/test_pipeline.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-028-evaluating-the-effectiveness-of-differen/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.13.4, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/test_pipeline.py


- python -m pytest tests/contract/test_schemas.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-028-evaluating-the-effectiveness-of-differen/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: platformdirs-4.13.4, anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_schemas.py


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
