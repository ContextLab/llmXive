# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.cli.run_fidelity --full  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3`
  - script usage: `run_fidelity.py [-h] [--smoke] [--full]`
  - argparse error: `run_fidelity.py: error: unrecognized arguments: --seeds 42 123 2026 --max-epochs 30 --early-stopping-delta 0.001 --early-stopping-patience 3`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python -m src.cli.run_fidelity --smoke`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_fidelity --smoke (rc=1); python -m src.cli.run_fidelity --full  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 (rc=2); python -m pytest -q tests/contract (rc=1)

## Failing / missing run-book commands

- python -m src.cli.run_fidelity --smoke -> rc=1
equests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/adapters.py", line 688, in send
    raise ConnectTimeout(e, request=request)
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='openml.org', port=443): Max retries exceeded with url: /data/get_csv/1590/adult.csv (Caused by ConnectTimeoutError(<HTTPSConnection(host='openml.org', port=443) at 0x7f363f7ee6d0>, 'Connection to openml.org timed out. (connect timeout=30)'))

- python -m src.cli.run_fidelity --full  --seeds 42 123 2026  --max-epochs 30  --early-stopping-delta 0.001  --early-stopping-patience 3 -> rc=2

usage: run_fidelity.py [-h] [--smoke] [--full]
run_fidelity.py: error: unrecognized arguments: --seeds 42 123 2026 --max-epochs 30 --early-stopping-delta 0.001 --early-stopping-patience 3

- python -m pytest -q tests/contract -> rc=1
E                                                                        [100%]
==================================== ERRORS ====================================
_________________ ERROR at setup of test_metric_results_schema _________________

    @pytest.fixture(scope="module")
    def schema():
        if not SCHEMA_YAML.is_file():
>           pytest.fail(f"Schema file not found: {SCHEMA_YAML}")
E           Failed: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-187-evaluating-the-statistical-properties-of/specs/001-statistical-fidelity/contracts/metric_results.schema.yaml

tests/contract/test_metric_schema.py:39: Failed
=========================== short test summary info ============================
ERROR tests/contract/test_metric_schema.py::test_metric_results_schema - Fail...
1 error in 0.32s


