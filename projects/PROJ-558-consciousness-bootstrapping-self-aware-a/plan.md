# Plan: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## Overview

This project investigates whether recursive self-modeling can bootstrap emergent
self-awareness in small language models. We implement a TinyLlama-based architecture
with temporal recursive self-attention and train it to predict its own reasoning
consistency as a proxy for meta-cognitive awareness.

## Methodology

### Core Approach

We train a recursive model that:
1. Generates multiple reasoning paths for each input
2. Uses majority vote of these paths as an **internal self-consistency proxy**
3. Trains a confidence head to predict this proxy signal
4. Evaluates calibration between predicted confidence and actual self-consistency

### Data Sources

- **Training**: Pile (arXiv subset) - truncated to token limit
- **Evaluation**: GSM8K and MMLU benchmarks
- **Control**: Shuffled-attention variants to isolate recursion effects

### Key Metrics

- Self-consistency score (majority vote agreement)
- Calibration metrics (Brier score, ECE)
- Error detection capability (ROC-AUC)
- Statistical significance (paired t-tests, Cohen's d)

## Architecture

### Model Components

1. **Base Llama**: TinyLlama-1.1B (or smaller if needed)
2. **Recursive Attention**: Temporal recursive self-attention module
3. **Confidence Head**: MLP for confidence prediction
4. **Training Loop**: Joint loss (cross-entropy + confidence loss)

### Training Protocol

- **Recursion Depth**: Max 2 (hard constraint)
- **Samples per Item**: N=2 for training proxy (N=10 for evaluation)
- **Loss Function**: Cross-entropy + confidence prediction loss
- **Tie-Breaking**: Signal = 0 (incorrect) for ties

## Constraints

### Resource Limits

- **Time Budget**: 120 minutes total on CPU-only runner
- **Memory Limit**: 7GB peak RSS
- **Token Limit**: 100000 (default, per spec interpretation)

### Technical Constraints

- No GPU acceleration
- No low-bit quantization
- Must fail loudly on OOM (no automatic depth reduction)
- Must use real data sources (no synthetic fallbacks)

## Validation Strategy

### Unit Tests

- Shape consistency for recursive attention
- Loss function computation
- Metric calculations (ECE, Brier, ROC-AUC)
- Statistical test logic

### Integration Tests

- End-to-end training pipeline
- Benchmark execution
- Statistical analysis report generation

### Statistical Rigor

- Multiple seeds (minimum 3 valid seeds)
- Paired t-tests with Bonferroni correction
- Sensitivity analysis on confidence thresholds
- Effect size reporting (Cohen's d)

## Philosophical Grounding

### Addressing Reviewer Concerns

The philosophical concerns raised by reviewers (Ada Lovelace, Alan Turing,
Daniel Kahneman, David Krakauer, Socrates, Stephen Wolfram) about the distinction
between *simulated* introspection and *genuine* meta-cognitive adaptation are
addressed through rigorous operationalization:

1. **Measurable Metrics**: We focus exclusively on quantifiable metrics defined
 in the spec (self-consistency, calibration, error detection)
2. **Control Conditions**: Shuffled-attention controls isolate recursion effects
3. **Statistical Significance**: Proper hypothesis testing validates findings
4. **Resource Constraints**: The 120-minute budget ensures architectural fidelity

### Scope Boundaries

Tasks T061-T070 (Philosophical Grounding metrics) were removed as unapproved
scope creep. The project scope is strictly limited to the measurable metrics
defined in the spec.md.

## Execution Plan

### Phase 1: Setup
- Create directory structure
- Initialize Python project
- Configure tooling

### Phase 2: Foundational
- Correct plan.md (T003a-T003c)
- Implement config.py with token_limit=100000
- Validate configuration
- Implement data loaders (Pile, GSM8K, MMLU)
- Create model entities
- Implement base wrapper

### Phase 3: User Story 1 (MVP)
- Implement recursive attention
- Implement loss functions
- Train models
- Validate recursion depth
- Add logging

### Phase 4: User Story 2
- Implement metrics calculation
- Run benchmarks (N=10 for self-consistency)
- Generate shuffled controls
- Validate output schema

### Phase 5: User Story 3
- Implement statistical tests
- Run sensitivity analysis
- Generate reports
- Filter invalid seeds

### Phase N: Polish
- Documentation updates
- Lint/format checks
- Memory profiling
- Quickstart validation

## Risk Mitigation

### Known Risks

1. **OOM on CPU**: Hard-fail with clear error (no depth reduction)
2. **Insufficient Seeds**: Fail if <3 valid seeds after filtering
3. **Data Fetch Failures**: Fail loudly (no synthetic fallback)
4. **Plan/Spec Divergence**: Resolved via T003a-T003c

### Contingency Plans

- If training exceeds time budget: Reduce batch size (not recursion depth)
- If metrics are unstable: Increase seed count (if resources allow)
- If data sources unavailable: Halt with clear error message

## Success Criteria

The project succeeds if:
1. All user stories complete independently
2. Statistical report shows significant results (p < 0.05 after correction)
3. All artifacts generated per spec
4. No fabrication of data or results
5. All tests pass in CI environment