# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/serialize_results.py: self-declared fabricated metric — “…/testing")          # Example dummy results to demonstrate serialization…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/serialize_results.py: self-declared fabricated metric — “…/testing")          # Example dummy results to demonstrate serialization…”; 7 command(s) failed: python code/generate_data.py --scenario A  # Options: A, B, C (rc=1); python code/ingest.py --input data/synthetic/scenario_A.csv --threshold 0.5 (rc=1); python code/models.py --input data/processed/scenario_A_threshold_0.5.csv (rc=1)

## Failing / missing run-book commands

- python code/generate_data.py --scenario A  # Options: A, B, C -> rc=1
2026-10-10 09:29:07 | INFO     | root | === Starting Synthetic Data Generation ===
2026-10-10 09:29:07 | INFO     | __main__ | Loading protocol from data/protocols/protocol.yaml
2026-10-10 09:29:07 | INFO     | __main__ | Protocol loaded successfully: N=N/A
2026-10-10 09:29:07 | INFO     | root | Generation Parameters:
2026-10-10 09:29:07 | ERROR    | root | Data generation failed: 'N'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/generate_data.py", line 151, in main
    logger.info(f"  - Sample Size (N): {protocol['N']}")
                                        ~~~~~~~~^^^^^
KeyError: 'N'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/generate_data.py", line 169, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/generate_data.py", line 151, in main
    logger.info(f"  - Sample Size (N): {protocol['N']}")
                                        ~~~~~~~~^^^^^
KeyError: 'N'

- python code/ingest.py --input data/synthetic/scenario_A.csv --threshold 0.5 -> rc=1
stion
    df = auto_generate_data(protocol)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/ingest.py", line 107, in auto_generate_data
    logger.info(f"  - N: {protocol['N']}")
                          ~~~~~~~~^^^^^
KeyError: 'N'

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/ingest.py", line 180, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/ingest.py", line 165, in main
    df = run_ingestion(input_path=None)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/ingest.py", line 150, in run_ingestion
    df = auto_generate_data(protocol)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/ingest.py", line 107, in auto_generate_data
    logger.info(f"  - N: {protocol['N']}")
                          ~~~~~~~~^^^^^
KeyError: 'N'

- python code/models.py --input data/processed/scenario_A_threshold_0.5.csv -> rc=1
2026-10-10 09:29:08 | WARNING  | __main__ | Could not load protocol: name 'yaml' is not defined
2026-10-10 09:29:08 | WARNING  | __main__ | Data file not found for strict: data/processed/data_threshold_strict.csv
2026-10-10 09:29:08 | WARNING  | __main__ | Data file not found for moderate: data/processed/data_threshold_moderate.csv
2026-10-10 09:29:08 | WARNING  | __main__ | Data file not found for partial: data/processed/data_threshold_partial.csv
2026-10-10 09:29:08 | INFO     | __main__ | Analysis pipeline completed

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/models.py", line 395, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/models.py", line 392, in main
    return combined_results
           ^^^^^^^^^^^^^^^^
NameError: name 'combined_results' is not defined

- python code/sensitivity.py --input data/synthetic/scenario_A.csv --threshold 0.5 --bootstrap 1000 --datasets 50 -> rc=1
 | __main__ | Starting Sensitivity Analysis (T032): Bootstrap vs Parametric CI Comparison
2026-10-10 09:29:09 | WARNING  | __main__ | Data file not found: data/processed/data_threshold_strict.csv
2026-10-10 09:29:09 | WARNING  | __main__ | Data file not found: data/processed/data_threshold_moderate.csv
2026-10-10 09:29:09 | WARNING  | __main__ | Data file not found: data/processed/data_threshold_partial.csv
2026-10-10 09:29:09 | ERROR    | __main__ | Error during sensitivity analysis: name 'json' is not defined
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/sensitivity.py", line 298, in main
    json.dump(output_data, f, indent=2)
    ^^^^
NameError: name 'json' is not defined

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/sensitivity.py", line 311, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/sensitivity.py", line 298, in main
    json.dump(output_data, f, indent=2)
    ^^^^
NameError: name 'json' is not defined

- python code/report.py --models results/models/ --sensitivity results/sensitivity/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/report.py", line 10, in <module>
    logger = setup_logging(__name__)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre/code/logging_config.py", line 18, in setup_logging
    logger.setLevel(log_level)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: '__main__'

- python -m pytest tests/unit/ -> rc=2
_schemas import (
code/validate_schemas.py:16: in <module>
    logger = setup_logging("validate_schemas")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
code/logging_config.py:18: in setup_logging
    logger.setLevel(log_level)
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:1464: in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py:207: in _checkLevel
    raise ValueError("Unknown level: %r" % level)
E   ValueError: Unknown level: 'validate_schemas'
=========================== short test summary info ============================
ERROR tests/unit/test_aggregate_results.py - ValueError: Unknown level: 'seri...
ERROR tests/unit/test_ordinal_validation.py
ERROR tests/unit/test_pipeline_timing.py - ValueError: Unknown level: 'serial...
ERROR tests/unit/test_serialize.py - ValueError: Unknown level: 'serialize_re...
ERROR tests/unit/test_validate_schemas.py - ValueError: Unknown level: 'valid...
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 5 errors in 2.09s ===============================


- python -m pytest tests/contract/ -> rc=1
ults.json', 'bizarreness_linear_results.json', 'ordinal_approx_results.json']

tests/contract/test_model_output_schema.py:73: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_model_output_schema.py::test_schema_exists - Asser...
FAILED tests/contract/test_model_output_schema.py::test_output_files_exist - ...
ERROR tests/contract/test_model_output_schema.py::test_json_validity - Failed...
ERROR tests/contract/test_model_output_schema.py::test_top_level_keys - Faile...
ERROR tests/contract/test_model_output_schema.py::test_results_structure - Fa...
ERROR tests/contract/test_model_output_schema.py::test_data_types - Failed: E...
ERROR tests/contract/test_model_output_schema.py::test_associational_framing
ERROR tests/contract/test_model_output_schema.py::test_simulation_flag - Fail...
ERROR tests/contract/test_model_output_schema.py::test_schema_compliance_with_yaml
ERROR tests/contract/test_synthetic_schema.py::test_synthetic_data_schema - K...
ERROR tests/contract/test_synthetic_schema.py::test_synthetic_data_scenario_consistency
========================= 2 failed, 9 errors in 0.52s ==========================


