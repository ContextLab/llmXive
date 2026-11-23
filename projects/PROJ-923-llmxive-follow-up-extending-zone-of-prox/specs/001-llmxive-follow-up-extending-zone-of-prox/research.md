# Research: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

## Research Question

How does dynamically pruning negative candidates based on student confidence (CAP) affect the data efficiency (AUCC) and generalization to novel error modes of prompt-based distillation, compared to a static negative candidate set?

## Hypothesis

The CAP-ZPPO variant will demonstrate **higher data efficiency** (steeper convergence, higher AUCC) than the static baseline by focusing the student's attention on "fluctuating" (proximal) error modes, thereby reducing cognitive load. Additionally, CAP-ZPPO will show **comparable or superior final accuracy** on held-out tasks, indicating that pruning does not lead to catastrophic forgetting of mastered or rejected patterns.

## Dataset Strategy

The study relies on two data sources:

1. **Synthetic Rollout Log**: Generated at runtime using a stochastic simulation engine. This log contains simulated student responses, confidence scores, and ground truth labels for a selected set of tasks (mix of LLM and VLM). The generation is seeded to ensure reproducibility and injects Gaussian noise (σ=0.05) into confidence scores to simulate variance.
2. **Held-Out Test Data (MMLU)**: Used for final accuracy evaluation to prevent circular validation. We will utilize the **MMLU-Pro** dataset.
 * **Source**: Verified Hugging Face datasets.
 * **URL**: `
 * **Usage**: The "held-out" set will be constructed by selecting specific subject categories from this source that are *not* present in the training buffer.

**Subject Category Mapping**:
To ensure Non-Circular Validation (Constitution Principle VII) and test generalization to novel error modes:
* **Training Buffer Subjects (10 categories)**: `history`, `geography`, `philosophy`, `literature`, `sociology`, `political_science`, `economics`, `business`, `law`, `ethics`.
* **Held-Out Test Subjects**: `physics`, `chemistry`, `biology`, `mathematics`, `computer_science`, `astronomy`, `medicine`, `psychology`, `anatomy`, `veterinary_medicine`.
* **Rationale**: These sets are disjoint. The synthetic generator uses the Training subjects to generate error modes. The Held-Out subjects provide a distinct distribution of questions to test if the student has generalized the *concept* of error correction rather than memorized specific patterns.

**Dataset Feasibility**: The MMLU-Pro dataset is open and directly downloadable via Hugging Face, making it suitable for unattended CI execution. The synthetic data generation avoids the need for large-scale real-world rollout logs.

## Methodology

### 1. Synthetic Data Generation & Learning Dynamics

* **Input**: 10 task schemas (derived from MMLU categories).
* **Expert Model Initialization**: For each seed, the "Expert Model" confidence distribution parameters (mean, variance) are **resampled** from a fixed hyper-distribution. This ensures the 100 runs represent distinct learning environments, not just noise on a fixed path.
* **Process**:
 * Initialize a "Student Model" with random initial confidence.
 * For each buffer cycle (up to a predetermined limit):
 * **Generate Prompt**: Determine candidate set (Static vs. CAP).
 * **Calculate Attention Weight**: $W_{att} = \frac{1}{\text{prompt\_length} + 1}$. This models the "cognitive load" hypothesis: fewer candidates = higher attention per candidate.
 * **Update Confidence**: The student's confidence for candidate $c$ at cycle $t$ is updated as:
 $$C_{student, t} = C_{student, t-1} + \alpha \cdot W_{att} \cdot (C_{expert} - C_{student, t-1}) + \mathcal{N}(0, \sigma^2)$$
 Where $\alpha$ is the learning rate, $C_{expert}$ is the fixed ground truth, and $\mathcal{N}$ is Gaussian noise.
 * **Inject Noise**: Gaussian noise (σ=0.05) is applied to ensure statistical variance.
* **Output**: `synthetic_rollout_log.jsonl` containing `task_id`, `cycle`, `candidate_id`, `student_confidence`, `expert_confidence`, `ground_truth`, `noise_applied`, `prompt_length`.

### 2. Baseline Simulation (Static ZPPO)

* **Mechanism**: The NCQ prompt includes **all** known failure modes for every training step. $W_{att}$ is constant (low).
* **Metric**: Track accuracy vs. cycles. Compute AUCC over 50 cycles.

### 3. CAP Simulation (Dynamic Pruning)

* **Mechanism**:
 * **Classify**: Calculate mean confidence for each candidate.
 * `Rejected`: Mean confidence < 0.1 (ε).
 * `Mastered`: Mean confidence > 0.9 (1-ε).
 * `Fluctuating`: 0.1 ≤ Mean confidence ≤ 0.9.
 * **Prune**: Exclude `Rejected` and `Mastered` candidates. Retain only `Fluctuating`.
 * **Edge Case Handling**: If pruning results in an empty prompt, fallback to the full set (FR-007).
 * **Learning Effect**: Because the prompt length is reduced for `Fluctuating` candidates, $W_{att}$ increases, accelerating the convergence of confidence for those specific items. This provides the **causal link** between pruning and improved efficiency.
* **Metric**: Track accuracy vs. cycles. Compute AUCC. Measure average prompt length (mid-training: cycles 20-40).

### 4. Statistical Analysis

* **Runs**: 100 total runs (10 tasks × 10 random seeds).
* **Comparison**: Paired t-test on AUCC between Static and CAP variants.
* **Significance**: α = 0.05 (FR-005, SC-004).
* **Generalization**: Compare final accuracy on held-out MMLU tasks (SC-003).

## Statistical Rigor

* **Multiple Comparisons**: Since the primary comparison is a single paired t-test (AUCC CAP vs. AUCC Static) across 100 runs, family-wise error correction is not strictly required for the main hypothesis. However, if multiple metrics (AUCC, final accuracy, prompt length) are tested, a Bonferroni correction will be applied.
* **Power Justification**: Multiple runs (10 tasks × 10 seeds) provides a robust distribution for the t-test. Crucially, because the **Expert Model distribution is resampled per seed**, the runs are statistically independent samples of the learning problem, satisfying the t-test independence assumption.
* **Causal Inference**: This is a controlled simulation. The "treatment" (CAP) is applied deterministically based on the algorithm. The **Attention Weight mechanism** explicitly models the causal link between prompt length and learning rate, ensuring the simulation measures algorithmic efficacy, not just correlation.
* **Measurement Validity**: The simulation uses a fixed "Expert Model" as ground truth, ensuring the student's learning signal is valid and non-circular (Principle VII). Mastery is validated against the fixed expert target, not the student's own dynamic state.
* **Collinearity**: Candidates are treated as independent error modes. If candidates are definitionally related, the analysis will report them descriptively and acknowledge potential collinearity in the discussion.
* **Cognitive Load Proxy**: The plan explicitly frames the "cognitive load" hypothesis as a **simulation proxy**. The correlation between prompt length and confidence variance is a validation of the *internal consistency* of the attention-weighted learning model, not a claim about real human cognitive states.

## Compute Feasibility

* **CPU-First**: The simulation uses `numpy` and `pandas` for all calculations. No GPU acceleration is required or used. The synthetic data generation and confidence updates are computationally lightweight.
* **Memory**: The dataset size is small, well within available RAM limits.
* **Time**: 100 runs are estimated to complete in < 2 hours on a 2-core CPU, well within the 6-hour CI limit.

## Risk Mitigation

* **Empty Prompts**: If CAP prunes all candidates, the system defaults to the static set (FR-007). This is logged and reported.
* **Data Leakage**: Held-out MMLU tasks are strictly separated from the training buffer subjects (see Subject Category Mapping).
* **Non-Convergence**: If the simulation fails to converge, the analysis will report the failure mode and exclude the run from the t-test, noting the limitation.