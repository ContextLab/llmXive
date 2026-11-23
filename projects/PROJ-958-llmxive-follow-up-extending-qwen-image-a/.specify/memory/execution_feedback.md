# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 10 run-book script(s) missing (plan/impl path mismatch): python 01_fetch_data.py; python 02_validate_data.py; python 03_compute_complexity.py

## Failing / missing run-book commands

- python 01_fetch_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/01_fetch_data.py': [Errno 2] No such file or directory
- python 02_validate_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/02_validate_data.py': [Errno 2] No such file or directory
- python 03_compute_complexity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/03_compute_complexity.py': [Errno 2] No such file or directory
- python 04_route_prompts.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/04_route_prompts.py': [Errno 2] No such file or directory
- python 05_generate_images.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/05_generate_images.py': [Errno 2] No such file or directory
- python 06_compute_fidelity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/06_compute_fidelity.py': [Errno 2] No such file or directory
- python 07_classify_domains.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/07_classify_domains.py': [Errno 2] No such file or directory
- python 08_regression_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/08_regression_analysis.py': [Errno 2] No such file or directory
- python 08_regression_analysis.py --stratify -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/08_regression_analysis.py': [Errno 2] No such file or directory
- python 11_efficiency_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-958-llmxive-follow-up-extending-qwen-image-a/11_efficiency_report.py': [Errno 2] No such file or directory
