# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/README.md: synthetic/fake INPUT data not authorized by the spec — “…k calls are made.  2.  **Synthetic Data**:     -   The original…”
- code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…s retrieval quality. 2.  Synthetic Data: Generates 500 queries m…”
- code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…is_correct: bool  # --- Synthetic Data Generation --- # Simulat…”
- code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…-> List[Sample]:     """Generates a balanced synthetic dataset representing het…”
- code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…Generating {NUM_SAMPLES} synthetic samples...")     samples = gener…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/README.md: synthetic/fake INPUT data not authorized by the spec — “…k calls are made.  2.  **Synthetic Data**:     -   The original…”; code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…s retrieval quality. 2.  Synthetic Data: Generates 500 queries m…”; code/omniretrieval_adapter.py: synthetic/fake INPUT data not authorized by the spec — “…is_correct: bool  # --- Synthetic Data Generation --- # Simulat…”; 1 command(s) failed: python code/omniretrieval_adapter.py (rc=1)

## Failing / missing run-book commands

- python code/omniretrieval_adapter.py -> rc=1
    strategy: Unified (OmniRetrieval)...
  -> Accuracy: 7.20%
Running strategy: Single Source: Search...
  -> Accuracy: 3.60%
Running strategy: Single Source: SQL...
  -> Accuracy: 2.80%
Running strategy: Single Source: SPARQL...
  -> Accuracy: 1.60%
Running strategy: Single Source: Cypher...
  -> Accuracy: 1.20%
Results saved to data/omniretrieval_results.csv
Plot saved to figures/accuracy_comparison.png

Simulation Complete.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-644-omniretrieval-unified-retrieval-across-h/code/omniretrieval_adapter.py", line 342, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-644-omniretrieval-unified-retrieval-across-h/code/omniretrieval_adapter.py", line 339, in main
    print(f"Core Result: Unified routing ({all_results[0]['accuracy']:.2%}) vs Best Single Source ({max(accuracies for r in all_results if 'Unified' not in r['strategy']):.2%})")
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: unsupported format string passed to list.__format__
