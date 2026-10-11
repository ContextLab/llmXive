# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ear stress.  This module generates synthetic molecular dynamics traje…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…42) -> Dict:     """     Generate a complete synthetic MD trajectory.…”
- code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…Main entry point to generate synthetic trajectories.     Genera…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…]:     """     Checks if synthetic data exists in data_dir. If n…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…metadata_json          # Generate a small synthetic trajectory for fallback…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…")          logger.info("Synthetic data generated.")     return…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…Path]:     """     Loads synthetic data from data_dir.     """…”
- code/data_loader.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info("Loading synthetic data...")         synthetic_f…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/metadata.json, data/raw/synthetic_trajectory_0.h5, data/raw/synthetic_trajectory_1.h5) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/analysis.py --input data/processed/d2_min_trajectory.csv --output data/processed/permutation_results.json --aggregation shear_band --k 3`
  - script usage: `analysis.py [-h] [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]`
  - argparse error: `analysis.py: error: unrecognized arguments: --aggregation shear_band --k 3`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…ear stress.  This module generates synthetic molecular dynamics traje…”; code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…42) -> Dict:     """     Generate a complete synthetic MD trajectory.…”; code/data_generator.py: synthetic/fake INPUT data not authorized by the spec — “…Main entry point to generate synthetic trajectories.     Genera…”; every produced artifact is gitignored (data/raw/metadata.json, data/raw/synthetic_trajectory_0.h5, data/raw/synthetic_trajectory_1.h5) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 run-book script(s) missing (plan/impl path mismatch): python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/preprocessing.py  --input data/raw/synthetic_trajectories  --output data/processed/d2_min_trajectory.csv  --seed 42; python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/validation.py  --input data/processed/d2_min_trajectory.csv  --output data/processed/sensitivity_table.csv  --threshold-range 0.05; python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/memory_profiler.py  --input data/processed/d2_min_trajectory.csv  --output data/processed/memory_profile.json; 1 command(s) failed: python code/analysis.py --input data/processed/d2_min_trajectory.csv --output data/processed/permutation_results.json --aggregation shear_band --k 3 (rc=2)

## Failing / missing run-book commands

- python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/preprocessing.py  --input data/raw/synthetic_trajectories  --output data/processed/d2_min_trajectory.csv  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-080-phase-transitions-in-amorphous-solids-un/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/preprocessing.py': [Errno 2] No such file or directory

- python code/analysis.py --input data/processed/d2_min_trajectory.csv --output data/processed/permutation_results.json --aggregation shear_band --k 3 -> rc=2

usage: analysis.py [-h] [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
analysis.py: error: unrecognized arguments: --aggregation shear_band --k 3

- python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/validation.py  --input data/processed/d2_min_trajectory.csv  --output data/processed/sensitivity_table.csv  --threshold-range 0.05 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-080-phase-transitions-in-amorphous-solids-un/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/validation.py': [Errno 2] No such file or directory

- python projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/memory_profiler.py  --input data/processed/d2_min_trajectory.csv  --output data/processed/memory_profile.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-080-phase-transitions-in-amorphous-solids-un/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/projects/PROJ-080-phase-transitions-in-amorphous-solids-un/code/memory_profiler.py': [Errno 2] No such file or directory

