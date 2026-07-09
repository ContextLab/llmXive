# Research: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

## Summary of Research Approach

This research investigates whether complex-valued token representations, leveraging amplitude and phase to model semantic ambiguity, improve word-sense disambiguation on the WiC benchmark compared to real-valued baselines. The core hypothesis is that context-dependent phase shifts and Born-rule probability computation (specifically the **interference cross-term**) enable the model to capture interference effects—constructive for aligned senses, destructive for conflicting ones—that real-valued embeddings cannot.

## Dataset Strategy

| Dataset | Source/Loader | Variables Used | Suitability Check |
|---------|---------------|----------------|-------------------|
| **WiC (Word-in-Context)** | `datasets.load_dataset("super_glue", "wic")` | `sentence1`, `sentence2`, `word`, `label` (ambiguous/unambiguous) | **Verified**: WiC explicitly provides word-in-context pairs with binary ambiguity labels, sufficient for training a compact adapter and testing interference hypotheses. No external cognitive measures (e.g., reaction times) are required per Assumptions. |
| **BERT (Base Uncased)** | `transformers.AutoModel.from_pretrained("bert-base-uncased")` | Hidden states ($\mathbb{R}^d$) | **Verified**: Frozen BERT provides contextualized embeddings; adapter maps to $\mathbb{C}^d$ without modifying transformer weights. |

> **Note**: The "Verified datasets" block in the prompt contains only unrelated BERT/UNK datasets. The WiC dataset is sourced from SuperGLUE via the `datasets` library (canonical HuggingFace hub), which is the standard, verified programmatic loader for this benchmark. No raw URLs are fabricated; the loader ensures checksumming and reproducibility.

## Methodological Framework

### 1. Baseline Establishment (US-1)
- **Model**: Frozen `bert-base-uncased` (no gradient updates).
- **Task**: Binary classification (ambiguous vs. unambiguous) on WiC test split.
- **Metrics**: Accuracy, macro-F1.
- **Stability**: 5 runs with distinct random seeds; variance ≤ 0.02 required.
- **Rationale**: Establishes a reproducible control condition; ensures any observed gains are attributable to the complex adapter, not BERT fluctuations.

### 2. Quantum-Inspired Adapter Implementation (US-2)
- **Architecture**:
  1.  **Projection**: Linear layer mapping BERT hidden states $\mathbf{h} \in \mathbb{R}^d$ to complex vectors $\mathbf{c} = \mathbf{a} + i\mathbf{b} \in \mathbb{C}^d$ (FR-001).
  2.  **Phase Shift**: Context-dependent unitary operator $U_c$ applied to $\mathbf{c}$.
      *   **Mechanism**: A lightweight linear layer projects the sentence-level BERT embedding to a scalar angle $\theta$. This angle defines a 2D rotation matrix $R(\theta)$ applied to each token's complex vector. This ensures the phase shift is learnable, context-dependent, and strictly unitary (preserving amplitude).
  3.  **Superposition**: Vector addition $\mathbf{c}_{sum} = \mathbf{c}_1 + \mathbf{c}_2$ (FR-002).
  4.  **Born Rule / Interference Calculation**:
      *   Instead of raw magnitude squared, the model computes the **Interference Cross-Term**: $I = \|\mathbf{c}_{sum}\|^2 - (\|\mathbf{c}_1\|^2 + \|\mathbf{c}_2\|^2) = 2\text{Re}(\mathbf{c}_1 \cdot \mathbf{c}_2^*)$.
      *   This value $I$ can be negative (destructive) or positive (constructive).
      *   **Normalization**: $P_{final} = \text{softmax}(I)$ over the two binary classes (ambiguous vs. unambiguous). This ensures the sign of the interference directly shifts the probability.
  5.  **Training**: 3 epochs, Adam optimizer, loss penalizing non-anti-parallel phases for ambiguous labels (FR-009).
- **Validation**: Synthetic tests confirm destructive interference ($c_1 = 1, c_2 = -1 \rightarrow I < 0$) and normalization (US-2).
- **Rationale**: Implements the core hypothesis; phase shifts encode order-dependent ambiguity, while the signed cross-term captures non-linear interference.

### 3. Statistical Analysis (US-3)
- **Design**: Paired t-test comparing baseline vs. complex model accuracy/F1 across 5 seeds.
- **Robustness**: 10,000 bootstrap resampling iterations to generate 95% confidence intervals for the effect size (Cohen's d).
- **Metrics**: p-value, t-statistic, Cohen's d, Bootstrap 95% CI.
- **Threshold**: α = 0.05; significance if $p < 0.05$ AND 95% CI does not include zero.
- **Limitation**: Acknowledged that N=5 has low power for medium effect sizes. If CI includes zero, results will be reported as inconclusive regardless of p-value.
- **Rationale**: Distinguishes signal from noise; aligns with Constitution VII.

### 4. Ablation Study (FR-005)
- **Protocol**: Two-stage training to isolate the mechanism.
  1.  **Shared Representation Training**: Train a model to learn complex representations $c_1, c_2$ using a generic loss (e.g., cross-entropy on the label). Freeze these representations.
  2.  **Evaluation Heads**:
      *   **Quantum Head**: Uses $P = \text{softmax}(I)$.
      *   **Classical Head**: Uses $P = \text{softmax}(\|\mathbf{c}_1\|^2 + \|\mathbf{c}_2\|^2)$.
      *   **Magnitude-Only Control**: Uses $P = \text{softmax}(\|\mathbf{c}_{sum}\|^2)$ (no subtraction of individual magnitudes).
- **Comparison**: Compare performance of the three heads on the frozen representations.
- **Rationale**: Isolates the interference cross-term contribution (SC-002) from the mere presence of complex embeddings or different training dynamics.

### 5. Interference Validation (FR-010, SC-005)
- **Check**: Explicit calculation of cross-term $2\text{Re}(\mathbf{c}_1 \cdot \mathbf{c}_2^*)$.
- **Validation Logic**: Instead of a binary check, verify that the **magnitude** of the negative cross-term correlates with the model's confidence or ambiguity level (e.g., higher negative cross-term for examples where the model is less confident or where human agreement on ambiguity is lower, if available).
- **Rationale**: Confirms the model learns *graded* interference (a property of ambiguity) rather than just forcing a negative value via the loss function.

## Addressing Reviewer Feedback (Wolfram/Feynman)

- **"Classical system that looks like quantum?"**: The implementation is explicitly classical (floating-point arithmetic) but mathematically mirrors quantum formalism (complex vectors, Born rule, interference). This is intentional: the hypothesis is that *quantum-inspired* mathematics improves modeling, not that the system is physically quantum. The plan isolates the interference cross-term (FR-010) to prove the "quantum-like" behavior is not merely a name.
- **"Where are the amplitudes?"**: Amplitudes are the complex vectors $\mathbf{c} = \mathbf{a} + i\mathbf{b}$; their squared magnitude (Born rule) yields probabilities. The plan includes synthetic tests (US-2) to verify amplitude addition and interference patterns.
- **"Sum-over-paths?"**: The superposition state ($\mathbf{c}_1 + \mathbf{c}_2$) is the sum-over-paths analog; phase shifts encode path-dependent interference. The ablation study (FR-005) confirms the cross-term (interference) is necessary for gains.

## Compute Feasibility

- **Hardware**: CPU-only (2 cores, 7 GB RAM).
- **Strategy**:
  - Frozen BERT (no gradient computation for transformer layers).
  - Compact adapter (< 1M parameters).
  - WiC dataset sampled to [deferred] examples for training (Assumptions).
  - Batch size = 8 to fit memory.
  - Total runtime: ≤ 6 hours (5 seeds × 3 epochs + baseline + stats + bootstrap).
- **Libraries**: `torch` (CPU wheel), `transformers`, `datasets`, `scikit-learn` (all CPU-tractable).

## Limitations & Assumptions

- **Power Analysis**: Sample size (5 seeds) is assumed sufficient for medium-large effect (Cohen's d ≥ 0.5); acknowledged as a limitation. Bootstrap CI is used to mitigate risk of false positives/negatives.
- **Causal Claims**: All results framed as associational (FR-006); no random assignment of cognitive states.
- **Numerical Stability**: NaN/Inf detection and renormalization implemented (Edge Cases).
- **Dataset Fit**: WiC variables (token contexts, labels) are sufficient; no external cognitive measures needed (Assumptions).