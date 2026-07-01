# Research: Neuromorphic Transformer Networks: Spiking Neural Dynamics in Language Models

## Research Question

How does embedding spiking-neuron dynamics into transformer attention mechanisms influence:
(a) The temporal coding characteristics of the network (spike timing precision, inter-spike intervals, temporal information capacity)?
(b) The trade-off between language modeling performance (perplexity) and computational cost (energy-per-token)?

## Dataset Strategy

The study utilizes **WikiText-2**, a standard benchmark for language modeling.

| Dataset | Source URL | Verification | Usage |
|:--- |:--- |:--- |:--- |
| **WikiText-2 (Raw)** | ` | Verified (HuggingFace) | Training set for model fitting. |
| **WikiText-2 (Validation)** | ` | Verified (HuggingFace) | Validation set for perplexity and temporal coding metrics. |

**Variable Fit Confirmation**:
- **Text Sequences**: Available in all listed datasets (parquet format contains text columns).
- **Token Counts**: Derivable from the text sequences via tokenization (no external metadata required).
- **Missing Variables**: None. The study does not require external metadata (e.g., timestamps, user IDs).

## Methodology

### 1. Baseline Transformer (US-1)
- **Architecture**: 2-layer Transformer, 4 attention heads, ~2.0M parameters.
- **Training**: 3 epochs minimum, batch size 32, LR 1e-3. Early stopping if validation loss plateaus (Δ < 0.01) for 2 epochs.
- **Metric**: Validation Perplexity.
- **Repetition**: 5 independent seeds (increased to 10 if power analysis requires).
- **Statistical Design**: Independent samples (different seeds for baseline and spiking).

### 2. Spiking Transformer (US-2)
- **Architecture**: Same as baseline, but Feed-Forward Networks (FFNs) replaced by **Leaky-Integrate-and-Fire (LIF)** neurons.
- **Learning**: Surrogate-gradient learning with piecewise-linear surrogate function (required for backpropagation through spikes).
- **Temporal Metrics** (SNN Only):
 - **Inter-Spike Interval (ISI) Variance**: Variance of time steps between consecutive spikes in a neuron.
 - **Bits/spike**: Calculated as the mutual information between the spike train and the input token sequence (estimated via binning).
 - **Synchrony Score**: Pairwise correlation of spike trains across neurons in the same layer.
- **Energy Measurement**: `codecarbon` to log CPU energy (kWh) per token.
 - *Fallback*: If `codecarbon` fails (common on CI without hardware sensors), log wall-clock time and flag as "estimated".
 - *Note*: On CPU, SNN simulation is computationally more expensive than dense ANNs. The "energy" metric here represents **computational cost**, not true neuromorphic efficiency.

### 3. Statistical Analysis (US-3)
- **Comparison**: **Unpaired Welch's t-tests** (Baseline vs. Spiking) on perplexity and energy-per-token. (Paired t-tests are invalid as seeds are independent).
- **Correction**: Bonferroni or Holm-Bonferroni for multiple comparisons (perplexity + energy).
- **Threshold Stability Sweep**: Instead of calculating FPR/FNR against a phantom "ground truth", the analysis sweeps energy-reduction thresholds {0.20, 0.25, 0.30, 0.35} and reports the **p-value stability** and **effect size direction** at each threshold. This quantifies how robust the "significant gain" conclusion is to the choice of threshold, without assuming a binary truth.
- **Power**: 5 seeds initially; if power < 0.8 for effect size δ ≥ 0.8, increase to 10 seeds.

## Computational Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM, No GPU).
- **Execution**: **CPU Only**. No CUDA, no mixed-precision training.
- **Model Size**: ~2M parameters ensures training fits within 6 hours for 10 seeds.
- **Library Compatibility**: `snnTorch` v0.9.x supports CPU execution. `codecarbon` may report "estimated" values on CI; the plan explicitly handles this as a secondary metric.
- **Edge Cases**:
 - **Zero-Spike Layers**: If >50% of neurons are silent for 3 epochs, training halts with a diagnostic report.
 - **Data Corruption**: Retry download 3 times; halt if failed.
 - **Energy Measurement Validation**: Before training, the system checks if `codecarbon` can access hardware sensors. If not, it logs a warning and defaults to "time-per-token" with an `is_estimated_energy=True` flag.

## Reviewer Feedback Integration

- **Stephen Wolfram**: The proposal relies on standard LIF dynamics, not "simple programs" or cellular automata. While the reviewer suggests mining the computational universe, the current spec mandates LIF neurons for direct comparison with existing SNN literature. This plan adheres to the spec but acknowledges in `research.md` that the LIF rule is a specific, continuous-time approximation rather than a discrete cellular automaton.
- **Linus Pauling**: The "physical constraints" of protein structure are not directly applicable to neural network energy consumption on CPUs. However, the plan ensures that energy measurements are transparent and explicitly labeled as "CPU computational cost" rather than "neuromorphic hardware efficiency," addressing the concern about inadequate physical modeling.
- **John Von Neumann**: The "instruction table" is the training algorithm. The plan specifies that spiking behavior is a physical constraint of the model architecture (LIF dynamics), not a metaphor, and that storage capacity (parameters) is fixed and measured.
- **Eric Kandel**: The temporal precision of spiking is the core metric. The plan explicitly measures ISI and synchrony, aligning with the biological sequence of cellular changes (transmitter release -> structural reorganization) by measuring the "release" (spikes) and "timing" (ISI).
- **Alan Turing**: The "instruction table" is the surrogate gradient rule. The plan clarifies that spiking is a physical constraint of the forward pass (discrete events) and the backward pass (surrogate gradients), ensuring mechanical consequence.