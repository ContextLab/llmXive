# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/contracts/analysis.schema.yaml: synthetic/fake INPUT data not authorized by the spec — “…description: Warning if synthetic data was detected.     proper…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…nate CSV exists; if not, generate a    deterministic synthetic dataset (validation‑only…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…such file.  Otherwise it generates a     deterministic synthetic dataset (validation‑only…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…e CSV found – generating synthetic data "                 "(vali…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…log.error(f"Failed to generate synthetic dataset: {exc}", exc_inf…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…# Default material for synthetic data         )     except Gra…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…material="graphene",  # Synthetic data uses graphene by default…”
- code/src/data_ingestion/generate_synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Validation…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/contracts/analysis.schema.yaml: synthetic/fake INPUT data not authorized by the spec — “…description: Warning if synthetic data was detected.     proper…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…nate CSV exists; if not, generate a    deterministic synthetic dataset (validation‑only…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…such file.  Otherwise it generates a     deterministic synthetic dataset (validation‑only…”; 4 command(s) failed: python code/src/data_ingestion/generate_synthetic.py --output data/raw/synthetic_defects.csv --seed 42 (rc=1); python code/main.py --config code/config.yaml (rc=1); python -m pytest tests/unit/ (rc=2); 1 declared deliverable(s) absent: data/results/end_to_end.json

## Failing / missing run-book commands

- python code/src/data_ingestion/generate_synthetic.py --output data/raw/synthetic_defects.csv --seed 42 -> rc=1
2026-10-25 13:27:46 - llmXive.data_ingestion - WARNING - === SYNTHETIC DATA GENERATION MODE ===
2026-10-25 13:27:46 - llmXive.data_ingestion - WARNING - This dataset is generated for pipeline validation ONLY.
2026-10-25 13:27:46 - llmXive.data_ingestion - WARNING - Do not use for scientific hypothesis testing.
2026-10-25 13:27:46 - llmXive.data_ingestion - ERROR - Failed to generate synthetic data: [Errno 17] File exists: 'data/raw/synthetic_defects.csv'
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data_ingestion/generate_synthetic.py", line 181, in main
    result = generate_synthetic_dataset(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data_ingestion/generate_synthetic.py", line 121, in generate_synthetic_dataset
    out_path.mkdir(parents=True, exist_ok=True)
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/pathlib.py", line 1116, in mkdir
    os.mkdir(self, mode)
FileExistsError: [Errno 17] File exists: 'data/raw/synthetic_defects.csv'


- python code/main.py --config code/config.yaml -> rc=1
-topology/code/main.py", line 187, in main
    threshold = calculate_threshold(
                ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data_ingestion/threshold.py", line 82, in calculate_threshold
    lattice_constant = get_lattice_constant(material)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data/materials.py", line 114, in get_lattice_constant
    constants = get_material_constants(material_name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data/materials.py", line 91, in get_material_constants
    constants["R_lattice"] = get_r_lattice()
                             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/code/src/data/materials.py", line 48, in get_r_lattice
    if "R_lattice" not in config:
       ^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: argument of type 'Config' is not iterable

- python -m pytest tests/unit/ -> rc=2
ckage, level)
tests/unit/test_disconnected_graphs.py:19: in <module>
    from src.metrics.paths_and_lcc import calculate_path_length_and_lcc
E   ModuleNotFoundError: No module named 'src.metrics.paths_and_lcc'
_________________ ERROR collecting tests/unit/test_metrics.py __________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/tests/unit/test_metrics.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_metrics.py:16: in <module>
    from src.metrics.clustering import calculate_clustering_coefficients
E   ModuleNotFoundError: No module named 'src.metrics.clustering'
=========================== short test summary info ============================
ERROR tests/unit/test_disconnected_graphs.py
ERROR tests/unit/test_metrics.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.70s ===============================


- python -m pytest tests/integration/ -> rc=1
==================
___________________ test_graph_construction_known_threshold ____________________
tests/integration/test_graph_construction.py:161: in test_graph_construction_known_threshold
    assert density > 0.0, "Graph density is 0. No edges found within threshold."
E   AssertionError: Graph density is 0. No edges found within threshold.
E   assert 0.0 > 0.0
=============================== warnings summary ===============================
tests/integration/test_graph_construction.py:125
  /home/runner/work/llmXive/llmXive/projects/PROJ-364-exploring-the-impact-of-network-topology/tests/integration/test_graph_construction.py:125: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_graph_construction.py::test_graph_construction_known_threshold
========================= 1 failed, 1 warning in 0.45s =========================



## Declared deliverables still missing

- data/results/end_to_end.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/end_to_end.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/results/end_to_end.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
