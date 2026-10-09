# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…te: This module provides synthetic data generation ONLY for inte…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…ityRecord]]:     """     Generates synthetic polymer graphs for testi…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…# Create synthetic permeability record         log_perm = rando…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…None:     """     Saves synthetic polymer data to a CSV file for testin…”
- code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…fo(f"Saved {len(graphs)} synthetic samples to {output_path}")  def…”
- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…vice     )      # Create dummy data loader     # Generate a…”
- code/models/trainer.py: synthetic/fake INPUT data not authorized by the spec — “…dummy data loader     # Generate a few synthetic samples to test the back…”

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/ingestion.py --download-pubchem`
- `python code/data/ingestion.py --generate-mock-target`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…te: This module provides synthetic data generation ONLY for inte…”; code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…ityRecord]]:     """     Generates synthetic polymer graphs for testi…”; code/data/simulation.py: synthetic/fake INPUT data not authorized by the spec — “…# Create synthetic permeability record         log_perm = rando…”; 2 command(s) failed: python code/data/ingestion.py --download-pubchem (rc=1); python code/data/ingestion.py --generate-mock-target (rc=1)

## Failing / missing run-book commands

- python code/data/ingestion.py --download-pubchem -> rc=1

NIST source failed: Dataset 'polymer_science/permeability_nist' doesn't exist on the Hub or cannot be accessed.
PubChem source failed: Dataset 'pubchem_polymer' doesn't exist on the Hub or cannot be accessed.
FATAL: No real data available from NIST/PubChem. Real experimental data is required. Simulation is not a valid substitute. Execution halted.

- python code/data/ingestion.py --generate-mock-target -> rc=1

NIST source failed: Dataset 'polymer_science/permeability_nist' doesn't exist on the Hub or cannot be accessed.
PubChem source failed: Dataset 'pubchem_polymer' doesn't exist on the Hub or cannot be accessed.
FATAL: No real data available from NIST/PubChem. Real experimental data is required. Simulation is not a valid substitute. Execution halted.

