# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity; 2 command(s) failed: python code/validate_trajectories.py  --input data/raw/trajectories.json (rc=1); python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results (rc=1)

## Failing / missing run-book commands

- python code/validate_trajectories.py  --input data/raw/trajectories.json -> rc=1
- ERROR -   - Trajectory 168: Entropy mismatch (target=3.5000, measured=3.5649, diff=0.0649)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 169: Entropy mismatch (target=3.5000, measured=3.5182, diff=0.0182)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 171: Entropy mismatch (target=3.5000, measured=3.5357, diff=0.0357)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 172: Entropy mismatch (target=3.5000, measured=3.5420, diff=0.0420)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 175: Entropy mismatch (target=3.5000, measured=3.5263, diff=0.0263)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 176: Entropy mismatch (target=3.5000, measured=3.5348, diff=0.0348)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 177: Entropy mismatch (target=3.5000, measured=3.5680, diff=0.0680)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 179: Entropy mismatch (target=3.5000, measured=3.5356, diff=0.0356)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 180: Entropy mismatch (target=3.5000, measured=3.5404, diff=0.0404)
2026-10-15 04:42:35,386 - ERROR -   - Trajectory 181: Entropy mismatch (target=3.5000, measured=3.5430, diff=0.0430)
2026-10-15 04:42:35,386 - ERROR -   ... and 250 more.

- python code/analyze_results.py  --input data/logs/simulation_results.csv  --output-dir results -> rc=1
Selected optimal spline df=4 with AIC=5755.0679

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py", line 302, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py", line 289, in main
    results = run_logistic_regression(df, config)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/analyze_results.py", line 137, in run_logistic_regression
    "pseudo_r_squared": float(model.prsquared),
                              ^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/statsmodels/base/wrapper.py", line 34, in __getattribute__
    obj = getattr(results, attr)
          ^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'GLMResults' object has no attribute 'prsquared'

- python code/sensitivity.py  --input data/raw/trajectories.json  --output-dir results/sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-920-llmxive-follow-up-extending-masking-stal/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-920-llmxive-follow-up-extending-masking-stal/code/sensitivity.py': [Errno 2] No such file or directory

