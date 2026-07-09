# Feature Specification: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

**Feature Branch**: `001-quantum-cognition-superposition`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "What properties of interference‑based complex‑valued token representations enable them to capture context‑dependent semantic ambiguity, and how do these properties correlate with performance on word‑sense disambiguation benchmarks compared to real‑valued embeddings?"

## User Scenarios & Testing

### User Story 1 - Baseline Real-Valued Evaluation (Priority: P1)

The researcher needs to establish a rigorous performance baseline using a standard real-valued transformer (frozen BERT) on the Word-in-Context (WiC) dataset to serve as the control condition for the quantum-inspired intervention.

**Why this priority**: Without a verified, reproducible baseline, any observed differences in the complex-valued model cannot be attributed to the quantum-inspired architecture. This is the prerequisite for all comparative analysis.

**Independent Test**: The system can be fully tested by loading the frozen BERT model, running inference on the WiC test split, and outputting a JSON file containing accuracy and macro-F1 scores. No complex-valued logic is required for this test.

**Acceptance Scenarios**:

1. **Given** the `bert-base-uncased` model is frozen and the WiC dataset is loaded, **When** the model processes the test split, **Then** the output JSON must contain `accuracy` and `macro_f` metrics with values within the expected range for frozen BERT (approx. 0.50–0.60 accuracy).
2. **Given** the baseline run is executed, **When** the random seed is changed to a different integer, **Then** the performance metrics must vary by no more than 0.02 across 5 runs, confirming stability.

---

### User Story 2 - Complex-Valued Interference Implementation (Priority: P1)

The researcher needs to implement the core quantum-inspired adapter: mapping real-valued hidden states to complex vectors, applying a context-dependent phase shift, performing vector addition (superposition), and applying the Born rule (with softmax normalization) to derive probabilities.

**Why this priority**: This is the core hypothesis test. If the implementation fails to produce valid complex arithmetic, phase shifts, or the Born rule calculation, the entire experimental premise collapses.

**Independent Test**: The system can be tested by injecting synthetic complex vectors (known phase and amplitude) into the adapter, performing the interference operation, and verifying that the output probability matches the theoretical squared magnitude of the sum (normalized via softmax).

**Acceptance Scenarios**:

1. **Given** two input tokens with complex representations $c_1 = 1 + 0i$ and $c_2 = -1 + 0i$ (representing perfect phase opposition), **When** the interference operation (phase shift + superposition) is computed, **Then** the resulting probability must be zero, confirming destructive interference.
2. **Given** two input tokens with $c_1 = 1 + 0i$ and $c_2 = 1 + 0i$ (representing phase alignment), **When** the interference operation is computed, **Then** the resulting probability must be normalized to unity after applying softmax normalization over the two binary output classes.
3. **Given** a valid WiC training example, **When** the adapter is trained for 3 epochs, **Then** the loss at epoch 3 must be lower than the loss at epoch 1, and the final loss must be < 0.7.

---

### User Story 3 - Comparative Statistical Analysis (Priority: P2)

The researcher needs to execute a paired statistical test comparing the performance of the complex-valued model against the real-valued baseline across multiple random seeds to determine if the improvement is statistically significant.

**Why this priority**: A single run difference is insufficient to claim a methodological advance. The study requires statistical validation to distinguish signal from noise.

**Independent Test**: The system can be tested by running the baseline and the complex model with identical seeds, collecting the paired scores, and verifying that the t-test output correctly calculates the p-value and effect size.

**Acceptance Scenarios**:

1. **Given** performance scores from 5 paired runs (baseline vs. complex), **When** a paired t-test is executed, **Then** the output must include a p-value, a t-statistic, and a Cohen's d effect size.
2. **Given** the complex model outperforms the baseline by ≥ 0.05 accuracy in all 5 runs, **When** the t-test is run, **Then** the p-value must be < 0.05.
3. **Given** the performance difference is < 0.01 across runs, **When** the t-test is run, **Then** the p-value must be > 0.05, correctly indicating no significant difference.

---

### Edge Cases

- What happens if the complex-valued adapter produces NaN or Inf values during the Born rule calculation due to numerical instability? The system must detect this and log an error rather than propagating invalid probabilities.
- How does the system handle the case where the WiC dataset contains ambiguous tokens that are not present in the BERT vocabulary? The system must utilize the tokenizer's standard unknown token handling (e.g., `[UNK]`) without crashing.
- What happens if the interference operation results in a probability > 1.0 due to normalization errors? The system must clamp or renormalize the output to the valid probability range [0, 1] via the defined softmax mechanism.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a linear projection layer that maps real-valued BERT hidden states ($\mathbb{R}^d$) to complex-valued vectors ($\mathbb{C}^d$) consisting of independent real and imaginary components. (See US-2)
- **FR-002**: System MUST compute the superposition of two token representations via vector addition ($c_{sum} = c_1 + c_2$) after applying context-dependent phase shifts, and derive the final prediction probability using the Born rule ($P_{raw} = \|c_{sum}\|^2$). (See US-2)
- **FR-003**: System MUST freeze all pre-trained BERT transformer weights during the training of the complex-valued adapter to ensure only the quantum-inspired layer is updated. (See US-1, US-2)
- **FR-004**: System MUST execute a paired t-test comparing the accuracy and F1 scores of the complex-valued model against the real-valued baseline across a minimum of 5 distinct random seeds. (See US-3)
- **FR-005**: System MUST perform an ablation study comparing the full quantum model ($P = \|c_1 + c_2\|^2$) against a classical baseline ($P = \|c_1\|^2 + \|c_2\|^2$) to isolate the contribution of the interference cross-term. (See US-2, US-3)
- **FR-006**: System MUST explicitly frame all reported performance differences as associational improvements on the WiC benchmark, avoiding causal claims about human cognition unless the experimental design includes random assignment of cognitive states (which it does not). (See US-3)
- **FR-007**: System MUST apply a context-dependent phase shift operator $U_c$ to the complex vectors before superposition, where $U_c$ is parameterized by the surrounding sentence context to encode order-dependent ambiguity. (See US-2)
- **FR-008**: System MUST normalize the raw Born rule output ($P_{raw}$) to a valid probability distribution over the binary classes (ambiguous vs. unambiguous) using a softmax function: $P_{final} = \frac{e^{P_{raw}}}{e^{P_{raw}} + e^{P_{alt}}}$. (See US-2)
- **FR-009**: System MUST implement a training loss function that explicitly penalizes non-anti-parallel phase relationships for tokens labeled as ambiguous, ensuring the model learns to produce destructive interference for conflicting senses. (See US-2)
- **FR-010**: System MUST explicitly calculate and validate the interference cross-term ($2\text{Re}(c_1 \cdot c_2^*)$) to ensure it can assume negative values for ambiguous inputs, distinguishing the model from classical vector addition. (See US-2)

### Key Entities

- **ComplexTokenRepresentation**: A vector $c = a + ib$ where $a, b \in \mathbb{R}^d$ are learned projections of the BERT hidden state.
- **SuperpositionState**: The result of vector addition ($c_1 + c_2$) of two phase-shifted complex token representations, representing the combined semantic state before measurement.
- **InterferenceEffect**: The change in probability distribution caused by the cross-term ($2\text{Re}(c_1 \cdot c_2^*)$) in the squared magnitude calculation, which can be negative (destructive) or positive (constructive).
- **NormalizationStrategy**: The softmax function applied over the two binary output classes to convert raw Born rule magnitudes into valid probabilities in [0, 1].
- **BenchmarkMetric**: The accuracy and macro-F1 score calculated on the WiC test split.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in accuracy between the complex-valued interference model and the frozen BERT baseline is measured against the null hypothesis of zero difference using a paired t-test (See US-3).
- **SC-002**: The contribution of the Born rule interference mechanism to performance is measured against the performance of a classical sum-of-probabilities ablation variant (See US-2).
- **SC-003**: The stability of the complex-valued representation is measured against the variance of performance metrics across 5 independent random seed initializations (See US-1).
- **SC-004**: The computational feasibility of the method is measured against the constraint of ≤ 6 hours wall-clock time on a single CPU core (pinned via `taskset --cpu-list 0`) with ≤ 7 GB RAM (See Assumptions).
- **SC-005**: The validity of the interference effect is measured by verifying that the probability output strictly adheres to the squared magnitude of the complex sum (Born rule) AND that the cross-term ($2\text{Re}(c_1 \cdot c_2^*)$) can be negative for ambiguous inputs (See US-2, FR-010).

## Assumptions

- The `bert-base-uncased` model from HuggingFace is compatible with the complex-valued projection adapter without requiring architectural changes to the transformer layers themselves.
- The WiC dataset from SuperGLUE contains sufficient examples (≥ 500) to train a small adapter (a compact parameter count) without overfitting within 3 epochs.
- The "quantum-inspired" nature of the model is purely mathematical (complex vector arithmetic) and does not require actual quantum hardware or quantum simulation libraries; standard floating-point arithmetic is sufficient.
- The interference operation defined as vector addition ($c_1 + c_2$) of *phase-shifted* vectors serves as a valid proxy for "superposition" in this specific cognitive modeling context. This is justified by Busemeyer et al. (2011), where the superposition state (vector sum) combined with context-dependent phase shifts models the dynamic, non-commutative nature of cognitive states. The phase shift $U_c$ encodes the dynamic context required to model order effects, and the resulting interference effect (probability modification) captures the ambiguity resolution.
- The dataset variables (token contexts, sense labels) in the WiC benchmark are sufficient to test the hypothesis without needing external cognitive state measures (e.g., reaction times or eye-tracking), which are not available.
- The sample size of 5 random seeds is sufficient to detect a medium-to-large effect size (Cohen's d ≥ 0.5) given the expected variance in LLM fine-tuning; power analysis is deferred to the implementation phase but acknowledged as a limitation.
- No GPU acceleration is available; all matrix operations must be performed on CPU using standard double-precision floating-point arithmetic to ensure reproducibility and avoid CUDA dependency.
- The "Born rule" application here is interpreted as the squared L2 norm of the summed complex vector, normalized to [0, 1] for the binary classification task via softmax over the two classes, as no specific normalization constant is provided in the literature.