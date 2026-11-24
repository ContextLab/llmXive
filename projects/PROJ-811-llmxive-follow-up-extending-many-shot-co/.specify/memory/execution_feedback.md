# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/generate_gold_standard_template.py: synthetic/fake INPUT data not authorized by the spec — “…""" Script to generate a synthetic gold standard template f…”
- code/scripts/generate_gold_standard_template.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, Any]:     """     Generate a synthetic gold standard template w…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9`
  - script usage: `prompt_gen.py [-h] --manifest MANIFEST`
  - argparse error: `prompt_gen.py: error: the following arguments are required: --manifest`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/generate_gold_standard_template.py: synthetic/fake INPUT data not authorized by the spec — “…""" Script to generate a synthetic gold standard template f…”; code/scripts/generate_gold_standard_template.py: synthetic/fake INPUT data not authorized by the spec — “…t[str, Any]:     """     Generate a synthetic gold standard template w…”; 2 run-book script(s) missing (plan/impl path mismatch): python code/src/download_data.py; python code/src/validate_metric.py --dags data/processed/dags.json --gold data/processed/gold_standard_annotations.json; 4 command(s) failed: python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9 (rc=2); python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b (rc=1); python code/src/analysis.py --input data/results/inference_log.csv (rc=1); 5 declared deliverable(s) absent: data/processed/curvature_scores.json; data/processed/dag_manifest.json; data/processed/embeddings.json

## Failing / missing run-book commands

- python code/src/download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-811-llmxive-follow-up-extending-many-shot-co/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/download_data.py': [Errno 2] No such file or directory

- python code/src/validate_metric.py --dags data/processed/dags.json --gold data/processed/gold_standard_annotations.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-811-llmxive-follow-up-extending-many-shot-co/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/validate_metric.py': [Errno 2] No such file or directory

- python code/src/prompt_gen.py --dags data/processed/dags.json --seeds 0 1 2 3 4 5 6 7 8 9 -> rc=2

usage: prompt_gen.py [-h] --manifest MANIFEST
                     [--strategy {original_cds,logical_ascending,logical_random}]
                     [--seed SEED] [--output OUTPUT]
prompt_gen.py: error: the following arguments are required: --manifest

- python code/src/inference.py --prompts data/processed/prompts/ --models qwen2.5-7b llama-3.1-8b -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/inference.py", line 13, in <module>
    from code.src.config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/config.py", line 17, in <module>
    class Config:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/config.py", line 84, in Config
    def get_seeds(self) -> List[int]:
                           ^^^^
NameError: name 'List' is not defined. Did you mean: 'list'?

- python code/src/analysis.py --input data/results/inference_log.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/code/src/analysis.py", line 7, in <module>
    from statsmodels.stats.effect_size import compute_effsize
ImportError: cannot import name 'compute_effsize' from 'statsmodels.stats.effect_size' (/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/stats/effect_size.py)

- python code/src/update_state.py -> rc=1
Usage: python -m code.src.update_state <command> [arguments]

Commands:
  hash <file_path>          - Calculate and print hash of a file
  update <file_path>        - Add/update artifact in state
  verify <file_path>        - Verify a single artifact
  verify-all                - Verify all tracked artifacts
  status                    - Show status of all artifacts



## Declared deliverables still missing

- data/processed/curvature_scores.json
- data/processed/dag_manifest.json
- data/processed/embeddings.json
- data/processed/gold_standard_annotations.json
- data/processed/prompt_manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/curvature_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/prompt_gen.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/curvature_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/dag_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_dag_manifest.py` — NOT invoked by the run-book
    - `code/scripts/run_prompt_strategies.py` — NOT invoked by the run-book
    - `code/scripts/validate_dag_correlation.py` — NOT invoked by the run-book
    - `code/tests/test_generate_dag_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_prompt_gen.py` — NOT invoked by the run-book
    - `code/tests/test_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dag_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/embeddings.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/prompt_gen.py` — IS a run-book command
    - `code/src/run_generate_embeddings.py` — NOT invoked by the run-book
    - `code/tests/test_prompt_gen_embeddings.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/embeddings.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gold_standard_annotations.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_gold_standard_template.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gold_standard_annotations.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/prompt_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/generate_prompt_manifest.py` — NOT invoked by the run-book
    - `code/scripts/validate_prompt_orderings.py` — NOT invoked by the run-book
    - `code/tests/test_generate_prompt_manifest.py` — NOT invoked by the run-book
    - `code/tests/test_integration.py` — NOT invoked by the run-book
    - `code/tests/test_validate_prompt_orderings.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompt_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
