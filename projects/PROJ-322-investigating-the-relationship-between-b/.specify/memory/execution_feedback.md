# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…"GraphMetrics",     # Synthetic Data     "generate_connectivi…”
- code/analysis_report.py: synthetic/fake INPUT data not authorized by the spec — “…nd("Results derived from synthetic data for methodology validati…”
- code/bootstrapping.py: synthetic/fake INPUT data not authorized by the spec — “…ctory.     Falls back to synthetic data if in methodology valida…”
- code/bootstrapping.py: synthetic/fake INPUT data not authorized by the spec — “…c mode and no real data, generate synthetic         if is_synthetic(…”
- code/bootstrapping.py: synthetic/fake INPUT data not authorized by the spec — “…ta not found. Generating synthetic data for bootstrapping.")…”
- code/bootstrapping.py: synthetic/fake INPUT data not authorized by the spec — “…known column names from synthetic data         efficiency_cols…”
- code/collinearity.py: synthetic/fake INPUT data not authorized by the spec — “…to be available or uses synthetic data for demonstration if in…”
- code/collinearity.py: synthetic/fake INPUT data not authorized by the spec — “…idation Mode. Generating synthetic data.")         # Generate sy…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 47 fabricated/simulated-result signal(s) — results are not real measurements: code/__init__.py: synthetic/fake INPUT data not authorized by the spec — “…"GraphMetrics",     # Synthetic Data     "generate_connectivi…”; code/analysis_report.py: synthetic/fake INPUT data not authorized by the spec — “…nd("Results derived from synthetic data for methodology validati…”; code/bootstrapping.py: synthetic/fake INPUT data not authorized by the spec — “…ctory.     Falls back to synthetic data if in methodology valida…”; 3 command(s) failed: python code/data_ingestion.py --dataset openneuro-fslr64k (rc=1); python code/graph_metrics.py --batch-size 5 --sparsity 0.15 (rc=1); python code/statistical_model.py --permutations 1000 --sweep-thresholds (rc=1); 5 declared deliverable(s) absent: data/results/bootstrapped_ci.json; data/results/gaps.json; data/results/manifest.csv

## Failing / missing run-book commands

- python code/data_ingestion.py --dataset openneuro-fslr64k -> rc=1
s/_validators.py", line 89, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-322-investigating-the-relationship-between-b/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 3259, in dataset_info
    hf_raise_for_status(r)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-322-investigating-the-relationship-between-b/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 953, in hf_raise_for_status
    raise _format(RepositoryNotFoundError, message, response, repo_type=repo_type, repo_id=repo_id) from e
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6acdd7e0-08a958ca5ffdaf8702e30343;b4f88ff5-4187-41ee-a2c9-4ee2af7c40b7)

Repository Not Found for url: https://huggingface.co/api/datasets/openneuro/ds000006/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- python code/graph_metrics.py --batch-size 5 --sparsity 0.15 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-322-investigating-the-relationship-between-b/code/graph_metrics.py", line 73, in <module>
    def calculate_modularity(matrix: np.ndarray, community_detection: Optional[nx.community.CommunityDetection] = None) -> float:
                                                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'networkx.algorithms.community' has no attribute 'CommunityDetection'

- python code/statistical_model.py --permutations 1000 --sweep-thresholds -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-322-investigating-the-relationship-between-b/code/statistical_model.py", line 10, in <module>
    import statsmodels.api as sm
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/api.py", line 123, in <module>
    from .graphics import api as graphics
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/graphics/api.py", line 1, in <module>
    from . import tsaplots as tsa
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/graphics/tsaplots.py", line 11, in <module>
    from statsmodels.tsa.stattools import acf, pacf, ccf
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/tsa/stattools.py", line 395, in <module>
    @deprecate_kwarg("unbiased", "adjusted")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: deprecate_kwarg() missing 1 required positional argument: 'new_arg_name'


## Declared deliverables still missing

- data/results/bootstrapped_ci.json
- data/results/gaps.json
- data/results/manifest.csv
- data/results/model_results.json
- data/results/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/bootstrapped_ci.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_report.py` — NOT invoked by the run-book
    - `code/bootstrapping.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/bootstrapped_ci.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/gaps.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_report.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/gaps.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/manifest.csv` is declared but was NOT written. Scripts referencing it:
    - `code/__init__.py` — NOT invoked by the run-book
    - `code/batch_processor.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/preprocessing.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/synthetic_data.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/manifest.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_report.py` — NOT invoked by the run-book
    - `code/bootstrapping.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/statistical_model.py` — IS a run-book command
  Make ONE of these WRITE `data/results/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/__init__.py` — NOT invoked by the run-book
    - `code/analysis_report.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
