# Feature Specification: Neuromorphic Transformer Networks: Spiking Neural Dynamics in Language Models

**Feature Branch**: `591-neuromorphic-transformer-spiking`  
**Created**: 2026-06-15  
**Status**: Draft  
**Input**: User description: "How does embedding spiking-neuron dynamics into transformer attention mechanisms influence (a) the temporal coding characteristics of the network and (b) the trade-off between language modeling performance (perplexity) and energy consumption measured independently from the model's internal activity?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Transformer Training and Evaluation (Priority: P1)

Train a conventional -layer, 4-head transformer on WikiText-2 and measure validation perplexity as the performance baseline.

**Why this priority**: Without a validated baseline model, no comparison with the spiking architecture is possible. This is the foundational experiment that all subsequent analysis depends on.

**Independent Test**: Can be fully tested by training the baseline transformer for minimum 3 epochs (with early stopping if validation loss plateaus) on WikiText-2 and verifying that validation perplexity is recorded and falls within expected ranges for this architecture size.

**Acceptance Scenarios**:

1. **Given** WikiText-2 dataset is downloaded and preprocessed, **When** the baseline transformer is trained for minimum 3 epochs with batch size 32, **Then** validation perplexity is computed and saved after each epoch
2. **Given** 5 independent random seeds are configured (or 10 if power analysis requires), **When** baseline training completes for all seeds, **Then** perplexity values are stored in CSV format with seed identifiers for statistical comparison

---

### User Story 2 - Spiking Transformer Implementation and Energy Measurement (Priority: P2)

Replace feed-forward sub-layers with leaky-integrate-and-fire (LIF) neurons using snnTorch, train with surrogate-gradient learning, measure computational cost via codeCarbon, and measure temporal coding characteristics (spike timing precision, inter-spike intervals, temporal information capacity).

**Why this priority**: This implements the core research intervention. Temporal coding analysis addresses the primary research question (a); computational cost measurements provide secondary insight into (b) with explicit caveats about CPU limitations.

**Independent Test**: Can be fully tested by training the spiking transformer variant and verifying that (i) LIF neurons are active during forward passes, (ii) spike timing metrics are recorded, (iii) computational cost is logged per token, and (iv) perplexity is computed for comparison.

**Acceptance Scenarios**:

1. **Given** snnTorch library is installed and LIF neurons are configured with surrogate gradient learning, **When** the spiking transformer processes WikiText-2 validation sequences, **Then** spike activity is recorded including inter-spike interval variance, bits/spike temporal information capacity, and spike train synchrony metrics
2. **Given** the spiking transformer completes training for 5 seeds (or 10 if power analysis requires), **When** codeCarbon reports computational cost metrics, **Then** energy-per-token values are saved alongside perplexity and temporal coding measurements for paired statistical analysis
3. **Given** codeCarbon fails to report energy metrics, **When** the system detects this failure, **Then** wall-clock time is logged as a secondary computational cost proxy with 'estimated' flag and the primary energy metric is marked unavailable

---

### User Story 3 - Statistical Analysis and Performance-Computational Cost Trade-off Reporting (Priority: P3)

Perform paired t-tests comparing perplexity and energy-per-token across seeds for baseline vs. spiking models, apply multiple-comparison correction, perform sensitivity analysis on energy-reduction thresholds, and report the performance-computational cost trade-off with confidence intervals and temporal coding comparisons.

**Why this priority**: This synthesizes all measurements into the research conclusion. Without statistical rigor, observed differences may be artifacts rather than evidence. Sensitivity analysis establishes robustness of conclusions.

**Independent Test**: Can be fully tested by running the statistical analysis script on the collected metrics and verifying that t-test results, p-values, confidence intervals, and sensitivity sweep results are computed and saved.

**Acceptance Scenarios**:

1. **Given** perplexity and energy-per-token CSVs from baseline and spiking models, **When** paired t-tests are performed with α=0.05, **Then** p-values and confidence intervals are computed and stored
2. **Given** multiple hypothesis tests are executed (perplexity and energy), **When** family-wise error correction is applied, **Then** adjusted p-values are reported and any significance claims reference the corrected threshold
3. **Given** energy-reduction threshold sweep over {0.20, 0.25, 0.30, 0.35}, **When** false-positive/false-negative rates are calculated against ground truth (positive = ≥30% reduction, negative = <30%), **Then** sensitivity curves are reported showing how classification of 'significant gain' varies across cutoffs
4. **Given** temporal coding metrics from spiking model, **When** compared against baseline transformer's non-spiking activation patterns, **Then** differences in inter-spike interval variance, bits/spike, and synchrony are reported with statistical significance

---

### Edge Cases

- What happens when WikiText-2 download fails or the dataset is corrupted? The system MUST retry download up to 3 times, then halt with an explicit error message.
- How does the system handle spiking neurons that never fire during training? The system MUST detect zero-spike layers and log a warning; if >50% of neurons are silent across 3 epochs (minimum), training MUST terminate with a diagnostic report.
- What happens when codecarbon fails to report energy metrics? The system MUST fall back to wall-clock time as a secondary computational cost proxy and flag the energy measurement as 'estimated' rather than direct; the primary energy metric is marked unavailable in results.
- How does the system handle GPU detection on CI runners? The system MUST explicitly force CPU execution and verify no CUDA device is available before training begins.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess WikiText from https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip (See US-1)
- **FR-002**: System MUST implement a 2-layer, 4-head transformer with 2.0M ±10% parameters using PyTorch (See US-1)
- **FR-003**: System MUST train baseline and spiking models for minimum 3 epochs with batch size 32 and learning rate 1e-3, with early stopping if validation loss plateaus for 2 consecutive epochs (Δloss < 0.01) (See US-1, US-2)
- **FR-004**: System MUST replace feed-forward sub-layers ONLY with leaky-integrate-and-fire (LIF) neurons using snnTorch library (See US-2)
- **FR-005**: System MUST apply surrogate-gradient learning with piecewise-linear surrogate function for spiking transformer training (See US-2)
- **FR-006**: System MUST instrument all training and evaluation runs with codecarbon to log CPU energy (kWh) per token, calculated as total_energy_kWh / total_tokens_processed, with wall-clock time fallback when codecarbon fails (See US-2)
- **FR-007**: System MUST compute validation perplexity after each epoch for both baseline and spiking models (See US-1, US-2)
- **FR-008**: System MUST execute multiple independent training runs with different random seeds for each model variant, with the number of runs determined by power analysis to ensure statistical robustness. for [deferred] power at effect size δ≥0.8 (See US-1, US-2, US-3)
- **FR-009**: System MUST perform paired t-tests comparing perplexity and energy-per-token across the seeds with α=0.05 (See US-3)
- **FR-010**: System MUST apply multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when reporting statistical significance for ≥2 hypothesis tests (See US-3)
- **FR-011**: System MUST sweep energy-reduction threshold over {0.20, 0.25, 0.30, 0.35} and report false-positive/false-negative rates where ground truth positive = ≥30% reduction and negative = <30% (required for reproducibility robustness per community standards) (See US-3)
- **FR-012**: System MUST explicitly force CPU execution and verify no CUDA device is available before any training begins (See US-1, US-2)
- **FR-013**: System MUST measure temporal coding characteristics including inter-spike interval variance, bits/spike temporal information capacity, and spike train synchrony for spiking model outputs (See US-2)

### Key Entities

- **TrainingRun**: Represents one complete training execution with a specific random seed, model variant (baseline/spiking), and associated metrics (perplexity, energy-per-token, temporal coding metrics)
- **MetricRecord**: Contains validation perplexity, energy-per-token, and temporal coding values for a single epoch of a specific training run
- **StatisticalComparison**: Aggregates paired t-test results, p-values, confidence intervals, and sensitivity analysis across seeds for baseline vs. spiking models

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Validation perplexity is measured against the baseline transformer's mean perplexity across seeds (See US-1)
- **SC-002**: Energy-per-token (computational cost) is measured against the baseline model's mean energy-per-token across seeds (See US-2)
- **SC-003**: Statistical significance (p-value) is measured against the corrected α threshold after multiple-comparison adjustment (See US-3)
- **SC-004**: Energy-reduction sensitivity is measured across threshold sweeps {0.20, 0.25, 0.30, 0.35} to quantify how classification of 'significant gain' (≥30% energy reduction) varies; temporal coding metrics (inter-spike interval variance, bits/spike) are measured against baseline transformer's non-spiking activation patterns (See US-3)
- **SC-005**: Wall-clock time per epoch is measured as a secondary computational cost proxy when codecarbon fails (See US-2)

## Assumptions

- WikiText-2 dataset contains all required variables: text sequences for perplexity computation and token counts for energy-per-token normalization. If the dataset lacks metadata needed for energy normalization, the analysis will use per-epoch total energy as an alternative metric.
- snnTorch library version 0.9.x or compatible is available on GitHub Actions free-tier runners and can execute on CPU without CUDA dependencies.
- codecarbon package can report CPU energy consumption on GitHub Actions runners; if hardware-level measurements are unavailable, wall-clock time will serve as a validated proxy with explicit 'estimated' flag.
- The 2-layer, 4-head transformer (~2M parameters) will complete minimum 3 epochs of training within 30 minutes per seed on a 2-CPU, 7GB RAM runner, allowing multiple training runs (across multiple seeds and models) to finish within the allocated job limit.
- Surrogate-gradient learning with piecewise-linear surrogate function will converge within minimum 3 epochs; if loss does not decrease after epoch 2, early stopping may trigger but training continues to minimum epoch count.
- Energy consumption measured via codecarbon on CPU represents computational cost proxy, NOT true neuromorphic energy efficiency. SNN energy advantages only manifest on neuromorphic hardware (Loihi, TrueNorth); CPU measurements are explicitly acknowledged as limited and do not support claims about SNN hardware efficiency. This caveat is documented in all results.
- The research design is observational (no random assignment of model architectures); all claims about performance-computational cost trade-offs will be framed as associational, not causal.
- The 5-seed replication provides sufficient statistical power for paired t-tests at α=0.05 for medium-to-large effect sizes (δ≥0.8); if power analysis indicates insufficiency, seed count increases to minimum 10 per FR-008.
- No GPU, CUDA, bitsandbytes, or mixed-precision training will be used; all models run in default precision on CPU to ensure compatibility with GitHub Actions free-tier runners.
- A significant energy-reduction threshold is based on community standards for energy-efficient neural architectures; sensitivity analysis will sweep ±10% to test robustness per FR-011.
- Temporal coding metrics (inter-spike interval variance, bits/spike, spike train synchrony) directly address research question component (a) and are primary outcomes; computational cost measurements address component (b) with explicit hardware limitations acknowledged.