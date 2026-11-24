"""Pinned random seed for all stochastic components (Constitution I).

Every stochastic stage of the pipeline (Monte‑Carlo power analysis,
dataset sampling, LLM generation, zero‑shot classification, bootstrap
resampling) MUST import and use ``SEED`` so that runs are reproducible.
"""

SEED = 42
