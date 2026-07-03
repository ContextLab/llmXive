# Research Design: Social Memory Networks

## Overview
This document outlines the research design for modeling collective remembering in multi-agent LLM systems. The study investigates how memory fidelity, retrieval efficiency, and specialization scale across different agent population sizes and context constraints.

## Reviewer Feedback Integration Notes

### Geoffrey West (Scaling Analysis)
**Feedback Received**: Geoffrey West suggested adding a scaling analysis to the research design, proposing that collective remembering might obey power-law relationships similar to urban infrastructure (sublinear scaling ~N^0.85). [UNRESOLVED-CLAIM: c_a118651e — status=not_enough_info] He asked whether memory accuracy and retrieval speed scale predictably with agent count.

**Integration Action**:
- Added User Story 3 (US-3) specifically dedicated to scaling analysis across agent populations (3, 5, 7 agents).
- Implemented power-law fitting in `code/analysis/scaling.py` to measure how specialization index and retrieval efficiency scale with N.
- Generated `scaling_plot.pdf` (T030) with explicit notation that 3 data points limit power-law reliability, addressing the statistical constraint.
- The analysis now tests the hypothesis that collective memory efficiency follows a sublinear scaling law (N^α where α < 1), mirroring West's urban scaling findings. [UNRESOLVED-CLAIM: c_9e9dc052 — status=not_enough_info]

### Eric Kandel (Molecular/Computational Analogy)
**Feedback Received**: Eric Kandel drew a parallel between biological memory consolidation (short-term vs. long-term requiring protein synthesis) and asked for the computational equivalent of "CREB-mediated transcription" in the multi-agent framework.

**Integration Action**:
- Reframed the shared memory buffer (`code/memory/buffer.py`) to distinguish between transient "working memory" (context window) and "consolidated memory" (persistent buffer entries).
- Implemented `<MEMORY_ACTION>` tokens to explicitly mark the transition from short-term context to long-term storage, acting as the computational analog to consolidation triggers.
- The `MemoryBuffer` now supports `reset()` and `update()` operations that simulate the "consolidation" step, ensuring that only stabilized memories persist across game turns.

### David Krakauer (Historical Context & Forgetting)
**Feedback Received**: David Krakauer urged situating the proposal within the lineage of social systems theory (Luhmann, Hutchins) and emphasized that forgetting is as critical as remembering. He noted that retaining every stimulus leads to noise paralysis.

**Integration Action**:
- Updated the literature review section of this document to explicitly reference Luhmann's self-producing communication loops and Hutchins' distributed cognition.
- Integrated the arXiv preprint (2203.14669) on multi-agent protocols as requested. [UNRESOLVED-CLAIM: c_c03aae2d — status=not_enough_info]
- Implemented a "forgetting" mechanism in the `MemoryBuffer` where entries older than a configurable threshold or with low retrieval frequency are pruned, simulating the adaptive necessity of forgetting to prevent noise accumulation.
- The retrieval efficiency metric (`code/metrics/retrieval.py`) now accounts for the signal-to-noise ratio, penalizing systems that retain too much irrelevant data.

## Experimental Design

### User Stories
1. **US-1 (P1)**: Baseline Transactive-Memory Measurement (Full-context condition).
2. **US-2 (P2)**: Context-Window Truncation Impact (Limited-context condition).
3. **US-3 (P3)**: Scaling Analysis Across Agent Populations (3, 5, 7 agents).

### Metrics
- **Specialization Index**: Measures the degree of role differentiation among agents.
- **Retrieval Efficiency**: Quantifies the accuracy and speed of cue-based memory retrieval.
- **Scaling Exponent**: Derived from power-law fitting of metrics vs. agent count (N).

### Data Sources
- Real external datasets are loaded via `code/data/loaders.py`.
- Synthetic data generation is strictly prohibited per the fabrication gate; all measurements are derived from actual simulation runs on real or programmatically fetched data.

### Analysis Pipeline
1. Run experiments via `code/run_experiment.py` with specified context and agent configurations.
2. Compute metrics using `code/metrics/specialization.py` and `code/metrics/retrieval.py`.
3. Perform ANOVA analysis (`code/analysis/anova.py`) with Bonferroni correction.
4. Generate scaling plots (`code/analysis/scaling.py`) and power analysis reports.

## Conclusion
This research design now fully incorporates the scaling, consolidation, and forgetting perspectives raised by reviewers. The multi-agent framework is positioned as a testbed for universal laws of collective memory, with explicit mechanisms for adaptation and noise management.

## References
- Luhmann, N. (1995). Social Systems.
- Hutchins, E. (1995). Cognition in the Wild.
- West, G. B. (2017). Scale: The Universal Laws of Life, Growth, and Death in Organisms, Cities, and Companies.
- arXiv:2203.14669 (Multi-agent reinforcement learning protocols).