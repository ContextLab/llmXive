# Idea — follow-up to The Hippocampus as a Spatial Map: Preliminary Evidence from Unit Activity in the Freely-Moving Rat (neuroscience)

Anchor paper: The Hippocampus as a Spatial Map: Preliminary Evidence from Unit Activity in the Freely-Moving Rat (O'Keefe J et al., 1971; DOI 10.1016/0006-8993(71)90358-1, https://doi.org/10.1016/0006-8993(71)90358-1).

Research question: In the CRCNS public hc-3 dataset (multi-tetrode rat hippocampus), how does sequence-decoder fidelity for replay events differ between non-REM sleep, REM sleep, and quiet wakefulness, and is the difference better explained by spike-count or by oscillatory-phase covariates?

Hypothesis: Non-REM replay yields the highest sequence-fidelity scores; after controlling for spike count + theta phase, the non-REM advantage shrinks but persists.

Methods: Standard Bayesian place-decoder; matched-spike-count and phase-stratified comparison; nested-CV for hyperparameters.

Feasibility: implementable with free-model LLM panels + publicly available data; no paid services or proprietary compute required.
