# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/checksums.json, data/raw/skills.json, data/raw/tasks.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/checksums.json, data/raw/skills.json, data/raw/tasks.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis.py --input data/results/metrics.csv; 2 command(s) failed: python code/agent.py  --library-sizes 10 30 50 100  --pruning  --overlap high (rc=1); python -m pytest tests/contract/ (rc=1)

## Failing / missing run-book commands

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

    
        # Load config to determine expected thresholds
        # We assume config.py is available and has get_experiment_config
        try:
            from code.config import get_experiment_config
            config = get_experiment_config()
            overlap_level = config.get('OVERLAP_LEVEL', 'medium')
        except ImportError:
            # Fallback if config not loaded yet, assume medium for test logic
            overlap_level = 'medium'
    
        # Assertions based on overlap level
        if overlap_level == 'low':
            assert mean_score < 0.30, f"Low overlap expected <0.30, got {mean_score:.4f}"
        elif overlap_level == 'medium':
>           assert 0.50 <= mean_score <= 0.80, f"Medium overlap expected [0.50, 0.80], got {mean_score:.4f}"
E           AssertionError: Medium overlap expected [0.50, 0.80], got 1.0000
E           assert 0.9999999799999999 <= 0.8

tests/contract/test_schemas.py:221: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_schemas.py::test_real_skills_overlap_metrics - Ass...
========================= 1 failed, 28 passed in 3.12s =========================


