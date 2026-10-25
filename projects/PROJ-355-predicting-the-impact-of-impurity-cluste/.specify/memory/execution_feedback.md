# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -m pytest tests/ -> rc=2
ry info ============================
ERROR tests/integration/test_artifact_verification.py - SystemExit: 1
ERROR tests/integration/test_data_contract_validation.py
ERROR tests/integration/test_data_pipeline.py
ERROR tests/integration/test_descriptor_filter_integration.py
ERROR tests/integration/test_descriptor_integration.py
ERROR tests/integration/test_descriptor_pipeline.py
ERROR tests/integration/test_download_schema_validation.py
ERROR tests/integration/test_model_training.py
ERROR tests/integration/test_preprocessing_integration.py
ERROR tests/unit/test_alloy_system_id.py
ERROR tests/unit/test_alloy_systems.py
ERROR tests/unit/test_descriptor_filter.py
ERROR tests/unit/test_descriptor_interface.py
ERROR tests/unit/test_descriptors.py
ERROR tests/unit/test_download_validation.py
ERROR tests/unit/test_energy_generation.py
ERROR tests/unit/test_gb_builder.py
ERROR tests/unit/test_preprocessing.py
ERROR tests/unit/test_preprocessing_filter.py
ERROR tests/unit/test_simulate_energy.py
ERROR tests/unit/test_vif_analysis.py
!!!!!!!!!!!!!!!!!!! Interrupted: 21 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 16 warnings, 21 errors in 2.20s ========================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
