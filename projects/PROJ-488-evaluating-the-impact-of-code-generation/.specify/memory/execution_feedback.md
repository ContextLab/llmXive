# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- data/metrics/statistical_analysis_results.json: EVERY metric is null/NaN ([0].power_analysis.power, [0].power_analysis.effect_size, [0].power_analysis.sample_size, [0].power_analysis.threshold_met…) — nothing was computed

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 hollow-result signal(s) — the analysis ran but computed nothing: data/metrics/statistical_analysis_results.json: EVERY metric is null/NaN ([0].power_analysis.power, [0].power_analysis.effect_size, [0].power_analysis.sample_size, [0].power_analysis.threshold_met…) — nothing was computed; 1 command(s) failed: python code/metric_extraction.py (rc=1)

## Failing / missing run-book commands

- python code/metric_extraction.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-488-evaluating-the-impact-of-code-generation/code/metric_extraction.py", line 13, in <module>
    from radon.mi import mi_visit
ModuleNotFoundError: No module named 'radon.mi'
