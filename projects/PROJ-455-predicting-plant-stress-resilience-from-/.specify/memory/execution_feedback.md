# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/generator.py: metric `recovery_score` assigned from an RNG draw (line 91)
- code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…red by T026. This script generates synthetic data, maps it to KEGG, a…”
- code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…neration...")          # Generate synthetic data if not present…”
- code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic data at {synthetic_path}")…”
- code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…)          # Load the synthetic data     logger.info(f"Loadin…”
- code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Loading synthetic data from {synthetic_path}")…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…42 ) -> str:     """     Generate synthetic metabolomic data with gr…”
- code/data/generator.py: synthetic/fake INPUT data not authorized by the spec — “…f"Generating {n_samples} synthetic samples for {stress_type} stress…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 20 fabricated/simulated-result signal(s) — results are not real measurements: code/data/generator.py: metric `recovery_score` assigned from an RNG draw (line 91); code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…red by T026. This script generates synthetic data, maps it to KEGG, a…”; code/analysis/generate_mapped_data.py: synthetic/fake INPUT data not authorized by the spec — “…neration...")          # Generate synthetic data if not present…”; 2 command(s) failed: python code/analysis/pathway.py --input data/results/model_results.json --output data/results/biological_validation.json (rc=1); python code/main.py (rc=1); 3 declared deliverable(s) absent: data/processed/mapped_data.parquet; data/raw/kegg_mapping.tsv; data/raw/kegg_mapping_fallback.csv

## Failing / missing run-book commands

- python code/analysis/pathway.py --input data/results/model_results.json --output data/results/biological_validation.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-455-predicting-plant-stress-resilience-from-/code/analysis/pathway.py", line 192, in <module>
    def run_pathway_validation_script(input_path: str = "data/processed/mapped_data.parquet") -> Dict[str, Any]:
                                                                                                           ^^^
NameError: name 'Any' is not defined. Did you mean: 'any'?

- python code/main.py -> rc=1
{"timestamp": "2026-10-09T00:17:25.385980", "level": "INFO", "logger": "data.generator", "message": "Starting pipeline with seed=42, stress=drought"}
{"timestamp": "2026-10-09T00:17:25.386104", "level": "ERROR", "logger": "data.generator", "message": "Pipeline failed: audit_seed_propagation() missing 2 required positional arguments: 'generator_func' and 'train_func'"}



## Declared deliverables still missing

- data/processed/mapped_data.parquet
- data/raw/kegg_mapping.tsv
- data/raw/kegg_mapping_fallback.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/mapped_data.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/generate_mapped_data.py` — NOT invoked by the run-book
    - `code/analysis/pathway.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/mapped_data.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/kegg_mapping.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/pathway.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/kegg_mapping.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/kegg_mapping_fallback.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/pathway.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/kegg_mapping_fallback.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
