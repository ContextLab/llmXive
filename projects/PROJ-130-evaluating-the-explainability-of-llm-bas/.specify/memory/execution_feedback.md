# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 17 run-book script(s) missing (plan/impl path mismatch): python 01_download_data.py --verify-only; python 01_download_data.py --download; python 02_generate_patches.py --sample-size 50 --seed 42

## Failing / missing run-book commands

- python 01_download_data.py --verify-only -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/01_download_data.py': [Errno 2] No such file or directory
- python 01_download_data.py --download -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/01_download_data.py': [Errno 2] No such file or directory
- python 02_generate_patches.py --sample-size 50 --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/02_generate_patches.py': [Errno 2] No such file or directory
- python 03_execute_tests.py --timeout 60 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/03_execute_tests.py': [Errno 2] No such file or directory
- python 04_extract_attention.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/04_extract_attention.py': [Errno 2] No such file or directory
- python 05_compute_saliency.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/05_compute_saliency.py': [Errno 2] No such file or directory
- python 06_compute_bleu_rouge.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/06_compute_bleu_rouge.py': [Errno 2] No such file or directory
- python 07_statistical_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/07_statistical_analysis.py': [Errno 2] No such file or directory
- python 02_generate_patches.py --bug-id Defects4J-Lang-1 --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/02_generate_patches.py': [Errno 2] No such file or directory
- python 03_execute_tests.py --bug-id Defects4J-Lang-1 --timeout 60 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/03_execute_tests.py': [Errno 2] No such file or directory
- python 04_extract_attention.py --bug-id Defects4J-Lang-1 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/04_extract_attention.py': [Errno 2] No such file or directory
- python 05_compute_saliency.py --bug-id Defects4J-Lang-1 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/05_compute_saliency.py': [Errno 2] No such file or directory
- python 06_compute_bleu_rouge.py --bug-id Defects4J-Lang-1 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/06_compute_bleu_rouge.py': [Errno 2] No such file or directory
- python 01_download_data.py --download -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/01_download_data.py': [Errno 2] No such file or directory
- python 02_generate_patches.py --sample-size 50 --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/02_generate_patches.py': [Errno 2] No such file or directory
- python 02_generate_patches.py --sample-size 25 --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/02_generate_patches.py': [Errno 2] No such file or directory
- python 03_execute_tests.py --timeout 60 --exclude-bugs slow-bugs.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-130-evaluating-the-explainability-of-llm-bas/03_execute_tests.py': [Errno 2] No such file or directory
