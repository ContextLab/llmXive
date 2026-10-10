# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/data_loader.py --download; 3 command(s) failed: python -m pytest tests/ (rc=2); python code/main.py --mode text-only --model phi3-mini --retriever all-MiniLM-L6-v2 (rc=1); python code/main.py --mode visual-only --model tiny-vlm (rc=1)

## Failing / missing run-book commands

- python code/data_loader.py --download -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/data_loader.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
de/.venv/lib/python3.11/site-packages/transformers/utils/generic.py:441
  /home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/transformers/utils/generic.py:441: FutureWarning: `torch.utils._pytree._register_pytree_node` is deprecated. Please use `torch.utils._pytree.register_pytree_node` instead.
    _torch_pytree._register_pytree_node(

tests/integration/test_saa_evaluation.py:88
  /home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/tests/integration/test_saa_evaluation.py:88: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_runtime_optimizer.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=================== 1 skipped, 2 warnings, 1 error in 3.64s ====================


- python code/main.py --mode text-only --model phi3-mini --retriever all-MiniLM-L6-v2 -> rc=1
ckages/sentence_transformers/__init__.py", line 3, in <module>
    from .datasets import SentencesDataset, ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py", line 3, in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py", line 4, in <module>
    from .. import SentenceTransformer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 12, in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download
ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python code/main.py --mode visual-only --model tiny-vlm -> rc=1
ckages/sentence_transformers/__init__.py", line 3, in <module>
    from .datasets import SentencesDataset, ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py", line 3, in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py", line 4, in <module>
    from .. import SentenceTransformer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 12, in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download
ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/projects/PROJ-832-llmxive-follow-up-extending-citevqa-benc/code/.venv/lib/python3.11/site-packages/huggingface_hub/__init__.py)

