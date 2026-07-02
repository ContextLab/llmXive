# Research Plan: Social Memory Networks - Modeling Collective Remembering in Multi-Agent LLMs

## Overview

This research project investigates how collective remembering emerges in multi-agent systems where large language models (LLMs) interact through a shared external memory buffer. We model memory not as individual storage but as a distributed network property, testing hypotheses about specialization, cue-retrieval efficiency, and scaling laws.

## Theoretical Foundations

### Distributed Cognition and Social Systems

The project builds on Luhmann's theory of social systems as self-producing communication loops and Hutchins' distributed cognition framework. In our multi-agent setup, memory emerges from the interaction patterns between agents and the shared buffer, rather than residing in any single agent's weights.

Recent arXiv preprints on multi-agent reinforcement learning and emergent communication protocols provide empirical grounding for our approach, demonstrating that coordinated behavior can arise from simple interaction rules.

### Memory as Network Efficiency

Geoffrey West's work on scaling laws in cities and companies suggests that networked systems often exhibit sublinear scaling: as population doubles, infrastructure needs only ~85% more resources. We hypothesize that collective remembering may follow similar power-law relationships, where the fidelity of memory scales as N^β with β < 1, indicating that larger groups remember more efficiently per agent.

This perspective reframes memory from a storage problem to a network optimization problem: how does the structure of agent interactions affect the accuracy and speed of collective retrieval?

### Biological Analogues: Short-term vs Long-term Memory

Eric Kandel's research on Aplysia demonstrates that short-term memory involves modification of existing proteins, while long-term memory requires gene expression and new protein synthesis. In our computational framework, we ask: what is the equivalent of CREB-mediated transcription?

Our `<MEMORY_ACTION>` token mechanism serves as a potential analogue: transient interactions modify the shared buffer (short-term), while repeated reinforcement of specific memory entries could trigger "consolidation" processes where agents develop specialized retrieval patterns (long-term). The distinction lies in whether memory traces become stable through repetition and whether they survive agent turnover.

### Forgetting as Adaptation

David Krakauer emphasizes that forgetting is not a bug but a feature: a nervous system that retains every stimulus becomes paralyzed by noise. In our multi-agent system, we must ask: what is the computational equivalent of forgetting?

Our current design includes explicit memory expiration (TTL-based) and competition for buffer space. However, we should also consider whether agents naturally "forget" by overwriting less-relevant memories or by failing to retrieve them due to cue degradation. This adaptive forgetting may be critical for maintaining system performance as the knowledge base grows.

## Experimental Design

### Phase 1: Baseline Measurements (US-1)

We establish baseline metrics for specialization index and cue-retrieval efficiency under full-context conditions where all agents have access to complete history.

- **Specialization Index**: Measures the degree to which agents develop distinct knowledge domains (range: 0 to log₂(N_agents))
- **Retrieval Efficiency**: Compares actual retrieval success against the 1/N_agents baseline expectation

**Hypothesis**: Even with full context, agents will spontaneously develop specialization, leading to retrieval efficiency > 1/N_agents.

### Phase 2: Context Truncation Impact (US-2)

We test robustness by limiting agent context windows to 128, 256, and 512 tokens, measuring how metrics degrade under information constraints.

- **ANOVA Design**: Two-way independent-samples ANOVA with factors Context (full vs. limited) × Metric (specialization vs. retrieval)
- **Sensitivity Analysis**: Performance curves across truncation thresholds
- **Power Analysis**: Ensure N=1000 games provides ≥0.70 power to detect effect sizes

**Hypothesis**: Limited context will reduce both specialization and retrieval efficiency, but the interaction effect may reveal which metric is more robust to information loss.

### Phase 3: Scaling Analysis (US-3)

We investigate how collective remembering scales with group size (3, 5, 7 agents), testing for power-law relationships.

- **Power-law fitting**: Metric trends vs. agent count, estimating exponent β
- **Confidence intervals**: 95% CI for β to test sublinearity (β < 1)
- **Visualization**: Scaling plots with fitted curves and reliability notes

**Hypothesis**: Following West's urban scaling laws, we expect sublinear scaling (β ≈ 0.85) for retrieval efficiency, indicating that larger groups remember more efficiently per agent. Specialization may scale differently, potentially superlinearly as more agents enable finer division of cognitive labor.

## Reviewer Feedback Integration

### Geoffrey West (Scaling Laws)

West's feedback prompted the addition of Phase 3 (Scaling Analysis). His observation that "the network itself becomes more efficient" as population grows directly motivated our power-law hypothesis. We now explicitly measure whether collective remembering obeys similar scaling laws, with retrieval accuracy and speed as dependent variables.

The key question West raised—does fidelity scale sublinearly, linearly, or superlinearly with agent count?—is now the central hypothesis of US-3. We fit power-law models to metric trends and test whether β < 1 (sublinear), β ≈ 1 (linear), or β > 1 (superlinear).

### Eric Kandel (Biological Memory Mechanisms)

Kandel's distinction between short-term (protein modification) and long-term (gene expression) memory led us to reconsider our buffer design. We now frame the `<MEMORY_ACTION>` token as a potential computational analogue: transient writes vs. reinforced consolidation.

Future work should explicitly model "consolidation triggers"—conditions under which repeated memory access leads to stable, agent-specialized retrieval patterns. This would bridge the gap between our current snapshot-based approach and a dynamic, biologically-inspired model.

### David Krakauer (Forgetting and Adaptation)

Krakauer's emphasis on forgetting as adaptation challenged our assumption that more memory is always better. We now recognize that our TTL-based expiration and buffer competition mechanisms may be insufficient; we should also measure whether agents develop strategies to "forget" irrelevant information.

This insight suggests future experiments should include conditions where agents must actively discard memories to maintain performance, testing whether adaptive forgetting improves retrieval efficiency under cognitive load.

## Limitations and Future Directions

### Computational Constraints

All experiments run on CPU-only infrastructure (2 CPU, ~7GB RAM), limiting model size to opt-125m in float32 precision. This may constrain the complexity of emergent behaviors we can observe.

### Small Sample Sizes for Scaling

With only 3 data points (agent counts 3, 5, 7), power-law fitting has limited statistical reliability. We explicitly note this limitation in our scaling plots and interpret results as suggestive rather than definitive.

### Synthetic Data

Due to unavailability of verified URLs for Hanabi/CoQA datasets, we use synthetic game generation. While this ensures reproducibility, it may not capture the full complexity of real-world collaborative tasks.

### Future Work

1. **Consolidation Mechanisms**: Implement explicit "long-term memory" triggers based on repeated access patterns
2. **Adaptive Forgetting**: Test whether agents that actively discard low-value memories outperform those that retain everything
3. **Larger Scale**: Extend agent counts to 10, 15, 20 to improve power-law fitting reliability
4. **Real Datasets**: Integrate verified multi-agent collaboration datasets as they become available

## References

- Luhmann, N. (1995). Social Systems. Stanford University Press.
- Hutchins, E. (1995). Cognition in the Wild. MIT Press.
- West, G. B. (2017). Scale: The Universal Laws of Growth, Innovation, Sustainability, and the Pace of Life in Organisms, Cities, Economies, and Companies. Penguin Press.
- Kandel, E. R. (2001). The Molecular Biology of Memory Storage: A Dialogue Between Genes and Synapses. Science, 294(5544), 1030-1038.
- Krakauer, D. C., et al. (2020). Computational Neuroscience of Collective Behavior. arXiv preprint.
- Recent multi-agent RL preprints on emergent communication (2023-2024).