# Feature Specification: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Feature Branch**: `PROJ-596-memory-palaces-in-llms-spatial-reasoning`  
**Created**: 2026-06-16  
**Status**: Draft  
**Input**: User description: "How does explicit spatial organization of episodic memories in transformer architectures affect recall accuracy on sequential memory benchmarks compared to non‑spatial embedding strategies?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Spatial Memory Implementation and Baseline Comparison (Priority: P1)

The system implements a spatial-memory transformer variant and compares its recall accuracy against a non-spatial baseline on sequential memory benchmarks.

**Why this priority**: This is the primary research question. Without implementing both variants and measuring recall accuracy, no comparison is possible. All downstream analysis depends on this foundational work.

**Independent Test**: Can be fully tested by fine-tuning both models on bAbI task 3 and measuring exact-match recall accuracy across 5 random seeds.

**Acceptance Scenarios**:

1. **Given** gpt2-medium base model (4-bit quantized) and bAbI task 3 training data, **When** fine-tuning both spatial and non-spatial variants for 3 epochs with batch size 8 and learning rate 5e-5, **Then** both models produce valid checkpoints that run inference without errors.
2. **Given** trained spatial and non-spatial models, **When** evaluating on bAbI task 3 test set across 5 random seeds (0-4), **Then** exact-match recall accuracy is recorded for each seed and both variants.
3. **Given** recall accuracy measurements, **When** comparing spatial vs non-spatial performance, **Then** the difference in mean accuracy is computed and reported with standard deviation.

---

### User Story 2 - Statistical Analysis Framework with Multiple Comparison Correction (Priority: P2)

The system performs paired statistical testing across random seeds with appropriate corrections for multiple hypothesis testing.

**Why this priority**: Without proper statistical testing, performance differences cannot be distinguished from random variation. Multiple comparison correction prevents inflated false-positive rates when testing across multiple datasets.

**Independent Test**: Can be fully tested by running paired t-tests on recall accuracy across seeds and verifying p-values and confidence intervals are computed correctly.

**Acceptance Scenarios**:

1. **Given** recall accuracy scores from 5 random seeds for both variants, **When** performing paired two-tailed t-tests, **Then** p-values and 95% confidence intervals are computed for each dataset comparison.
2. **Given** multiple dataset comparisons (bAbI, LAMBADA, Story Cloze), **When** applying family-wise error correction, **Then** Bonferroni or Holm-Bonferroni correction is applied to control α at 0.05 across all tests.
3. **Given** paired accuracy measurements, **When** computing effect sizes, **Then** Cohen's d is calculated and reported alongside p-values.

---

### User Story 3 - Structural Metric Quantification for Spatial Organization (Priority: P2)

The system measures and reports structural correlates of spatial organization to address reviewer concerns about measurable structural differences. This includes the interference distance metric to validate that spatial organization improves recall under interference.

**Why this priority**: This is critical for validation. Without an independent behavioral metric (interference distance), claims about "spatial memory" remain assertions of internal state rather than demonstrated efficacy. The metrics distinguish effective spatial reasoning from mere grid usage.

**Independent Test**: Can be fully tested by computing the interference distance metric and verifying it shows a measurable difference between spatial and non-spatial variants.

**Acceptance Scenarios**:

1. **Given** spatial memory slot assignments, **When** injecting semantically unrelated items into adjacent grid coordinates, **Then** the system measures the drop in recall accuracy (interference distance) and reports it.
2. **Given** recall accuracy under interference, **When** comparing spatial vs non-spatial variants, **Then** the spatial variant must show a statistically significant reduction in interference (higher robustness) or the result is documented as a null finding.
3. **Given** slot occupancy data, **When** computing the distribution of memory slots used per sample, **Then** the system logs the distribution to ensure no slot is overloaded beyond capacity.

---

### Edge Cases

- What happens when a dataset sample exceeds the memory slot capacity (e.g., more episodic chunks than grid locations)? → System implements FIFO eviction with oldest slot overwritten; eviction rate is logged and must be ≤ 5% of total samples.
- How does system handle out-of-memory errors on GitHub Actions free tier? → System implements automatic dataset subsampling; If total model + data exceeds available RAM capacity, batch size is reduced to a lower value.. If memory usage still exceeds 6 GB at batch size 4, total samples are capped at [deferred] of the original.
- What happens when paired t-test assumptions are violated (non-normal distribution of accuracy differences)? → System runs Shapiro-Wilk normality test; if p < 0.05, Wilcoxon signed-rank test is used instead and both results are reported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement a 2-D grid of memory slots with coordinate assignment for each episodic chunk (See US-1)
- **FR-002**: System MUST compute cosine similarity between current hidden state and slot embeddings for soft-addressed retrieval (See US-1)
- **FR-003**: System MUST attempt training with 3 epochs, batch size 8, and learning rate 5e-5, but MUST reduce batch size to 4 if peak memory usage exceeds 6 GB RAM; the system MUST record the final effective hyperparameters used for each run and document any deviations (See US-1)
- **FR-004**: System MUST record exact-match recall accuracy for each random seed (0-4) on each dataset (See US-1)
- **FR-005**: System MUST perform paired two-tailed t-tests comparing baseline vs spatial-memory scores across 5 seeds (See US-2)
- **FR-006**: System MUST apply family-wise error correction (Bonferroni or Holm-Bonferroni) when >1 hypothesis test is run (See US-2)
- **FR-007**: System MUST compute Cohen's d effect size with 95% confidence intervals for all comparisons (See US-2)
- **FR-008**: System MUST compute and log slot occupancy distribution for every epoch (See US-3)
- **FR-009**: System MUST compute and log coordinate variance for every epoch (See US-3)
- **FR-010**: System MUST implement automatic batch size reduction to 4 if peak RSS of the Python process exceeds 6 GB RAM; if memory usage still exceeds 6 GB at batch size 4, the system MUST cap the dataset to [deferred] of the original size (See Assumption A-003)
- **FR-011**: System MUST compute interference distance by measuring recall drop when semantically unrelated items are assigned to adjacent grid coordinates, and report this metric for both spatial and non-spatial variants (See US-3)

### Key Entities

- **MemorySlot**: Represents a discrete location in the 2-D grid with coordinates (x, y) and associated embedding vector
- **EpisodicChunk**: A text unit (e.g., sentence) assigned to a memory slot with temporal ordering metadata
- **RecallAccuracy**: Exact-match metric computed per sample and aggregated across seeds for statistical testing

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Recall accuracy is measured against baseline non-spatial variant on bAbI task 3 (See US-1)
- **SC-002**: Recall accuracy is measured against baseline non-spatial variant on LAMBADA (See US-1)
- **SC-003**: Recall accuracy is measured against baseline non-spatial variant on Story Cloze Test (See US-1)
- **SC-004**: Statistical significance is measured against α = 0.05 threshold with multiple comparison correction (See US-2)
- **SC-005**: Effect size is measured against Cohen's d conventions (small ≥ 0.2, medium ≥ 0.5, large ≥ 0.8) (See US-2)
- **SC-006**: Interference distance is measured against the baseline non-spatial variant; the spatial variant is considered successful if it demonstrates a statistically significant reduction in interference (See US-3)
- **SC-007**: Total runtime is measured against 5-hour GitHub Actions free-tier limit (See Assumption A-003)
- **SC-008**: Memory usage is measured against a constrained RAM environment on a free-tier runner. (See Assumption A-003)

## Assumptions

- gpt2-medium (355M parameters) fits within 6 GB RAM when loaded with 4-bit quantization (bitsandbytes) and CPU-only execution; without quantization, the model requires >10 GB RAM and is infeasible.
- Dataset sizes (bAbI task 3, LAMBADA, Story Cloze) total ≤ 200 MB and fit within 14 GB disk constraint
- Total fine-tuning and evaluation runtime for 5 seeds across 3 datasets is ≤ 5 hours on GitHub Actions free-tier (Limited CPU cores, no GPU) with 4-bit quantization
- No CUDA, bitsandbytes, or GPU-specific operations are required beyond 4-bit quantization libraries; all computations use default PyTorch precision on CPU
- A range of random seeds provides sufficient statistical power for paired t-tests.; if power is insufficient, this limitation is documented in results
- Multiple comparison correction uses Bonferroni method as default; Holm-Bonferroni is used if Bonferroni is overly conservative (α < 0.001)
- The spatial memory grid uses 8×8 = 64 slots; if slot capacity is exceeded, FIFO eviction is applied (see Edge Cases). This eviction policy is essential to test the spatial capacity hypothesis and is not merely an implementation detail.
- All datasets are publicly available and accessible without authentication; if access fails, the pipeline logs the error and skips that dataset
- The spatial embedding module uses cosine similarity for retrieval; alternative metrics (Euclidean, dot product) are not tested in this iteration
- Statistical analysis uses scipy.stats for t-tests; if normality assumptions are violated, non-parametric alternatives are documented
- The binding problem (spatial tags integrating with distributed representations) is addressed via soft-addressed read mechanisms; explicit binding architectures are deferred to future work (see Eric Kandel and David Krakauer reviewer comments)
- Dataset-variable fit is confirmed: bAbI task 3 provides temporal reasoning targets, LAMBADA provides long-context prediction targets, Story Cloze provides narrative coherence targets—each maps to the episodic recall outcome variable
- Inference framing is associational: findings are reported as correlations between spatial organization and recall accuracy, not causal claims (no randomization of architecture)
- Threshold justification: interference distance metric is based on standard cognitive science measures of proactive interference; sensitivity analysis sweeps absolute diff across a range of small magnitudes. and reports how false-positive/false-negative rates vary across thresholds. A reduced batch size is triggered when RAM usage approaches the hard constraint to ensure a safety margin, following the methodology described in [Citation]. The research question remains: [Research Question], and the method is: [Method]..