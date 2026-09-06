# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005b` (rejected 1x): The `logger.py` file ends abruptly inside the `setup_logger` definition and does not contain a complete implementation, nor is there any `save_seed_config` function present. Additionally, `seed_config.json` is an empty `{}` with no evidence that new batch entries are being appended according to the required schema. The task’s core requirements are therefore unmet.
- `T028c` (rejected 1x): The repository contains a `write_simulation_results` function that the unit tests can call, but the simulation never writes to the required `results/simulation_results.csv` file – the file is absent. Moreover, the main loop does not appear to invoke the aggregation/writing logic after each configuration or at the end, so the task’s core requirement is not fulfilled. The next implementer must ensure that results are aggregated and written to `results/simulation_results.csv` with the specified schema during execution.
- `T057` (rejected 1x): The `metrics.py` file does not contain a `run_sensitivity_analysis` function, and the required data files `results/simulation_results.csv` and the generated `results/sensitivity_analysis.csv` are absent. Consequently the sensitivity analysis implementation and its deliverables are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

