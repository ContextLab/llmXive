# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/utils/models.py: self-declared fabricated metric — “…e math.         # We'll set a dummy value to satisfy the dataclass fiel…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…elp="Run mode: 'sim' for simulated data, 'real' for the full pip…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/utils/models.py: self-declared fabricated metric — “…e math.         # We'll set a dummy value to satisfy the dataclass fiel…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…elp="Run mode: 'sim' for simulated data, 'real' for the full pip…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/download.py --source huggingface --dataset chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3; python code/summarize.py --mode sim; python code/simulate_study.py --participants 12 --tasks-per-condition 10 --seed 42; 6 declared deliverable(s) absent: data/analysis_results/results.csv; data/analysis_results/sensitivity_analysis.csv; data/interaction_logs/anonymized_logs.csv

## Failing / missing run-book commands

- python code/download.py --source huggingface --dataset chathuranga-jayanath/defects4j-context-5-len-10000-prompt-3 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-140-evaluating-the-efficacy-of-code-summariz/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/code/download.py': [Errno 2] No such file or directory

- python code/summarize.py --mode sim -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-140-evaluating-the-efficacy-of-code-summariz/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/code/summarize.py': [Errno 2] No such file or directory

- python code/simulate_study.py --participants 12 --tasks-per-condition 10 --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-140-evaluating-the-efficacy-of-code-summariz/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/code/simulate_study.py': [Errno 2] No such file or directory

- python code/analysis.py --input data/interaction_logs/anonymized_logs.csv --mode ci -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-140-evaluating-the-efficacy-of-code-summariz/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/code/analysis.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/analysis_results/results.csv
- data/analysis_results/sensitivity_analysis.csv
- data/interaction_logs/anonymized_logs.csv
- data/interaction_logs/missing_ground_truth.json
- data/raw/defects4j/ground_truth.csv
- data/summaries/rule_summaries.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis_results/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/config.py` — NOT invoked by the run-book
    - `code/analysis/correction_utils.py` — NOT invoked by the run-book
    - `code/analysis/run_statistics.py` — NOT invoked by the run-book
    - `code/data_prep/download_defects4j.py` — NOT invoked by the run-book
    - `code/data_prep/generate_summaries.py` — NOT invoked by the run-book
    - `code/data_prep/generate_summaries_real_llm.py` — NOT invoked by the run-book
    - `code/data_prep/setup_data_directories.py` — NOT invoked by the run-book
    - `code/generation/generate_rule_summaries.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis_results/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/analysis_results/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/config.py` — NOT invoked by the run-book
    - `code/analysis/run_statistics.py` — NOT invoked by the run-book
    - `code/tests/test_statistics.py` — NOT invoked by the run-book
    - `code/utils/generate_artifact_hashes.py` — NOT invoked by the run-book
    - `code/utils/update_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis_results/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interaction_logs/anonymized_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/config.py` — NOT invoked by the run-book
    - `code/analysis/run_statistics.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/tests/test_anonymize_logs.py` — NOT invoked by the run-book
    - `code/tests/test_data_integrity.py` — NOT invoked by the run-book
    - `code/tests/test_reproducibility.py` — NOT invoked by the run-book
    - `code/utils/anonymize_logs.py` — NOT invoked by the run-book
    - `code/utils/generate_artifact_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interaction_logs/anonymized_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interaction_logs/missing_ground_truth.json` is declared but was NOT written. Scripts referencing it:
    - `code/download/download_defects4j.py` — NOT invoked by the run-book
    - `code/download/download_defectsj.py` — NOT invoked by the run-book
    - `code/utils/package_reproducibility.py` — NOT invoked by the run-book
    - `code/utils/update_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interaction_logs/missing_ground_truth.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/defects4j/ground_truth.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/run_statistics.py` — NOT invoked by the run-book
    - `code/download/download_defects4j.py` — NOT invoked by the run-book
    - `code/download/download_defectsj.py` — NOT invoked by the run-book
    - `code/generation/generate_summaries_offline.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/tests/test_anonymize_logs.py` — NOT invoked by the run-book
    - `code/tests/test_data_integrity.py` — NOT invoked by the run-book
    - `code/tests/test_generate_summaries_offline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/defects4j/ground_truth.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/summaries/rule_summaries.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/config.py` — NOT invoked by the run-book
    - `code/analysis/run_statistics.py` — NOT invoked by the run-book
    - `code/data_prep/generate_summaries.py` — NOT invoked by the run-book
    - `code/generation/generate_rule_summaries.py` — NOT invoked by the run-book
    - `code/generation/generate_summaries_offline.py` — NOT invoked by the run-book
    - `code/utils/generate_baseline_results.py` — NOT invoked by the run-book
    - `code/utils/package_reproducibility.py` — NOT invoked by the run-book
    - `code/utils/update_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/summaries/rule_summaries.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
