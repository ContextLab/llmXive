# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/analysis/reproducibility.py: self-declared fabricated metric — “…dation only         # This is NOT a real measurement, just for pipeline structure…”
- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…nifests  - `synthetic/`: Synthetic data for validation - `script…”
- code/src/data/qc.py: synthetic/fake INPUT data not authorized by the spec — “…input manifest (real or synthetic data)     2. Checks each stud…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Prototype…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…r Prototype Validation.  Generates structurally valid synthetic TPM count matrices for A…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic TPM count matrix.      U…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…n_samples: Number of synthetic samples (studies/replicates)…”
- code/src/data/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ping genes         # For synthetic data, we might just pick rand…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 14 fabricated/simulated-result signal(s) — results are not real measurements: code/src/analysis/reproducibility.py: self-declared fabricated metric — “…dation only         # This is NOT a real measurement, just for pipeline structure…”; code/README.md: synthetic/fake INPUT data not authorized by the spec — “…nifests  - `synthetic/`: Synthetic data for validation - `script…”; code/src/data/qc.py: synthetic/fake INPUT data not authorized by the spec — “…input manifest (real or synthetic data)     2. Checks each stud…”; 2 run-book script(s) missing (plan/impl path mismatch): python src/cli/run_pipeline.py --mode synthetic --seed 42; python src/cli/run_pipeline.py --mode real --accession_ids GSE12345,GSE67890; 5 declared deliverable(s) absent: data/manifests/batch_correction_report.json; data/manifests/real_data_manifest.json; data/processed/metadata_verification_report.json

## Failing / missing run-book commands

- python src/cli/run_pipeline.py --mode synthetic --seed 42 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/src/cli/run_pipeline.py': [Errno 2] No such file or directory
- python src/cli/run_pipeline.py --mode real --accession_ids GSE12345,GSE67890 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-463-predicting-plant-defense-allocation-from/src/cli/run_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/manifests/batch_correction_report.json
- data/manifests/real_data_manifest.json
- data/processed/metadata_verification_report.json
- data/processed/post_qc_species_list.json
- data/processed/trait_fallback_summary.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/manifests/batch_correction_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/batch_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifests/batch_correction_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/manifests/real_data_manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manifests/real_data_manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata_verification_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/data/synthetic_generator.py` — NOT invoked by the run-book
    - `code/src/data/verify_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata_verification_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/post_qc_species_list.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_traits_try.py` — NOT invoked by the run-book
    - `code/tests/unit/test_traits_fallback.py` — NOT invoked by the run-book
    - `code/tests/unit/test_qc.py` — NOT invoked by the run-book
    - `code/src/data/traits_gate.py` — NOT invoked by the run-book
    - `code/src/data/traits_try.py` — NOT invoked by the run-book
    - `code/src/data/traits_fallback.py` — NOT invoked by the run-book
    - `code/src/data/qc.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/post_qc_species_list.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/trait_fallback_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_traits_try.py` — NOT invoked by the run-book
    - `code/tests/unit/test_traits_fallback.py` — NOT invoked by the run-book
    - `code/src/data/traits.py` — NOT invoked by the run-book
    - `code/src/data/traits_gate.py` — NOT invoked by the run-book
    - `code/src/data/traits_try.py` — NOT invoked by the run-book
    - `code/src/data/traits_fallback.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/trait_fallback_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
