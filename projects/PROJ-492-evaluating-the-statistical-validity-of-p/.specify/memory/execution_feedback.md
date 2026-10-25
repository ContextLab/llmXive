# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/audit/stat_verification_runner.py: self-declared fabricated metric — “…stds                 # Using placeholder values for demonstration with real…”
- code/src/audit/synthetic.py: metric `ratio_sigma` assigned from an RNG draw (line 200)

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/src/audit/stat_verification_runner.py: self-declared fabricated metric — “…stds                 # Using placeholder values for demonstration with real…”; code/src/audit/synthetic.py: metric `ratio_sigma` assigned from an RNG draw (line 200); run-book completed but produced no data/figure artifacts; 2 declared deliverable(s) absent: data/input/urls.csv; data/manual_validation/real_world_labels.csv

## Failing / missing run-book commands

- (no per-command failures; the run produced no real data/figure artifacts — ensure scripts WRITE their declared outputs under data/ and figures/)

## Declared deliverables still missing

- data/input/urls.csv
- data/manual_validation/real_world_labels.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/input/urls.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/run_validator_test.py` — NOT invoked by the run-book
    - `code/src/audit/curate_corpus.py` — NOT invoked by the run-book
    - `code/src/audit/fetcher.py` — NOT invoked by the run-book
    - `code/src/audit/ingestor.py` — NOT invoked by the run-book
    - `code/src/audit/provenance_archiver.py` — NOT invoked by the run-book
    - `code/src/cli/run_audit.py` — NOT invoked by the run-book
    - `code/tests/integration/test_fetcher_integration.py` — NOT invoked by the run-book
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/input/urls.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/manual_validation/real_world_labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/integration/test_full_pipeline.py` — NOT invoked by the run-book
    - `code/tests/unit/test_t003_wikidata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/manual_validation/real_world_labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
