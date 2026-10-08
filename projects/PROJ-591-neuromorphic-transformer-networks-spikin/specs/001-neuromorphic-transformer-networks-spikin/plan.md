# Implementation Plan: Neuromorphic Transformer Networks — Spiking Neural Dynamics in Language Models

## Overview

This plan implements a controlled comparison between a conventional
2-layer, 4-head Transformer (~2M parameters) and a spiking variant in which
the feed-forward sub-layers are replaced with leaky-integrate-and-fire (LIF)
neurons trained via surrogate-gradient learning. Both models are trained on
WikiText-2, evaluated on validation perplexity, and measured for
computational cost (energy-per-token via codeCarbon with wall-clock
fallback). Temporal coding characteristics (ISI variance, bits/spike, spike
train synchrony) are recorded for the spiking model. All experiments run on
CPU-only infrastructure.

## Architecture

- **Baseline**: `code/models/baseline_transformer.py` — 2-layer, 4-head
 Transformer encoder (~2M parameters), CPU-only enforcement.
- **Spiking**: `code/models/spiking_transformer.py` — identical backbone
 with feed-forward sub-layers replaced by LIF neurons (snnTorch) using
 surrogate-gradient learning (FR-005), including a verification function
 asserting non-NaN gradients on a mini-batch (Constitution Principle VII).
- **Data**: `code/data/dataset_loader.py` — WikiText-2
 (`wikitext/wikitext-2-raw-v1`) from HuggingFace as primary source, with
 the S3 `wikitext-2-v1.zip` fallback and SHA-256 checksum recording
 (Constitution Principles I and III).

## Statistical Design (resolves FR-009)

**Paired Statistical Design.** The baseline and spiking models are trained
under *matching random seeds* (seeds 1–5) so that every baseline run has
exactly one spiking counterpart with the identical seed. This pairing
controls for seed-level variation in initialization, data ordering, and
dropout, and enables **paired t-tests** (FR-009) on `perplexity` and
`energy_per_token_kWh` across the 5 matched seed pairs. The analysis in
`code/analysis/statistical_tests.py` reads
`data/processed/baseline_metrics.csv` and
`data/processed/spiking_metrics.csv`, matches rows by `seed`, and performs
paired t-tests, followed by Bonferroni and Holm-Bonferroni correction for
the two hypotheses (perplexity + energy). Confidence intervals are reported
for paired mean differences. A sensitivity sweep over energy-reduction
thresholds {0.20, 0.25, 0.30, 0.35} (ground truth ≥30% reduction) computes
FP/FN rates and is saved to `data/results/sensitivity_analysis.csv`.

Training loops (`train_baseline` in T013 and the spiking loop in T017) MUST
use the identical seed list so that pairing is preserved end-to-end.

## Complexity Tracking

- **Model complexity**: fixed architecture budget (~2M parameters) for both
 variants so that observed differences are attributable to the spiking
 substitution, not capacity. Parameter counts are asserted in unit tests.
- **Paired Statistical Design**: baseline and spiking runs share identical
 random seeds (1–5). Statistical comparison uses **paired t-tests**
 (FR-009), not unpaired designs, because seed-matched runs remove
 between-run initialization variance and increase statistical power at a
 fixed compute budget. Any earlier text describing an "Unpaired
 Statistical Design" is superseded by this section; the paired design is
 normative.
- **Compute complexity**: CPU-only, all seeds, both models, must complete
 within the <6h total runtime budget (T029). Training uses batch size 32,
 lr 1e-3, minimum 3 epochs with early stopping on validation-loss
 plateau.
- **Multiple comparisons**: two primary hypotheses (perplexity,
 energy-per-token) corrected via Bonferroni and Holm-Bonferroni (T023).
- **Edge cases**: zero-spike detection (FR-006) — if >50% of LIF neurons
 are silent for 3 consecutive epochs, training terminates with
 `TrainingTerminationError`, logs "WARNING: Zero-spike detection
 triggered", and writes `data/logs/zero_spike_report.json`.
- **Energy measurement caveat**: codeCarbon CPU measurements are a proxy
 for neuromorphic hardware energy; wall-clock fallback results carry an
 explicit "estimated" flag (documented in `docs/`, T027).

## Milestones

1. **Setup** (T001–T003): project structure, dependencies, lint/format.
2. **Foundational** (T004–T010): data loader, both models, energy logger,
 temporal coding metrics, LIF dynamics and training-loop tests.
3. **US1 — Baseline** (T012–T015): baseline training across seeds 1–5,
 perplexity logging to `data/processed/baseline_metrics.csv`.
4. **US2 — Spiking + Energy** (T017–T020): spiking training with surrogate
 gradients, zero-spike detection, energy and temporal coding metrics to
 `data/processed/spiking_metrics.csv`.
5. **US3 — Statistical Analysis** (T022–T026): paired t-tests with
 multiple-comparison correction, sensitivity sweep, report and plots.
6. **Polish** (T027–T031): docs, cleanup, performance, unit tests,
 quickstart validation.

## Risks and Mitigations

- **CPU runtime overrun**: mitigated by early stopping, small model, and
 the T029 optimization pass.
- **Zero-spike collapse in LIF layers**: mitigated by surrogate gradients
 and the FR-006 blocking detection with diagnostic report.
- **codeCarbon unavailability**: wall-clock fallback with "estimated" flag;
 never silently substituted.
- **Statistical power with 5 seeds**: mitigated by the paired design,
 which reduces variance of the mean difference relative to an unpaired
 design at the same number of runs.