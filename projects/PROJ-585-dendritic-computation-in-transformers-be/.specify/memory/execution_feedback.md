# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/utils/download_data.py`
- `python code/experiments/probe.py --input-dir data/experiments/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/utils/download_data.py (rc=1); python code/experiments/train.py --config config.yaml (rc=1); python code/experiments/probe.py --input-dir data/experiments/ (rc=1)

## Failing / missing run-book commands

- python code/utils/download_data.py -> rc=1
    ba79d07bc864c1c254ccfcedcce55bcc9a8c/README.md?%2Fdatasets%2Fnyu-mll%2Fglue%2Fresolve%2Fmain%2FREADME.md=&etag=%22274c0b2c4c5524fe09285a8b7d945fe98a1dfe7a%22 "HTTP/1.1 200 OK"
2026-10-05 03:32:45,500 - INFO - HTTP Request: GET https://huggingface.co/api/resolve-cache/datasets/nyu-mll/glue/bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/README.md?%2Fdatasets%2Fnyu-mll%2Fglue%2Fresolve%2Fmain%2FREADME.md=&etag=%22274c0b2c4c5524fe09285a8b7d945fe98a1dfe7a%22 "HTTP/1.1 200 OK"
2026-10-05 03:32:45,582 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/glue/resolve/bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/glue.py "HTTP/1.1 307 Temporary Redirect"
2026-10-05 03:32:45,659 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/nyu-mll/glue/resolve/bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/glue.py "HTTP/1.1 404 Not Found"
2026-10-05 03:32:45,905 - INFO - HTTP Request: HEAD https://s3.amazonaws.com/datasets.huggingface.co/datasets/datasets/glue/glue.py "HTTP/1.1 200 OK"
2026-10-05 03:32:45,943 - ERROR - Failed to download or process dataset: Invalid HF URI 'hf://datasets/glue@bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/.huggingface.yaml'. Repository id must be 'namespace/name', got 'glue'.
- python code/experiments/train.py --config config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/experiments/train.py", line 20, in <module>
    from models.transformer_base import TransformerBaseline
ModuleNotFoundError: No module named 'models'
- python code/experiments/probe.py --input-dir data/experiments/ -> rc=1
    hed_path
    ).resolve_path(url_or_filename)
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/.venv/lib/python3.11/site-packages/huggingface_hub/hf_file_system.py", line 307, in resolve_path
    parsed = parse_hf_uri(f"{constants.HF_PROTOCOL}{path}")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/.venv/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 319, in parse_hf_uri
    return _parse_repo_body(location, type_, raw=raw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/.venv/lib/python3.11/site-packages/huggingface_hub/utils/_hf_uris.py", line 617, in _parse_repo_body
    raise HfUriError(uri=raw, msg=f"Repository id must be 'namespace/name', got '{repo_id}'.")
huggingface_hub.errors.HfUriError: Invalid HF URI 'hf://datasets/glue@bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/.huggingface.yaml'. Repository id must be 'namespace/name', got 'glue'.
- python code/experiments/analyze.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/experiments/analyze.py", line 10, in <module>
    from statsmodels.stats.multitest import multipletests
ModuleNotFoundError: No module named 'statsmodels'
- python code/tests/test_architecture_match.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/tests/test_architecture_match.py", line 26, in <module>
    from models.transformer_base import TransformerBaseline
ModuleNotFoundError: No module named 'models'
