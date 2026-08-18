# Research: llmXive follow-up: extending "Translation as a Bridging Action"

## 1. Research Question & Hypothesis

**Primary Question**: Can a lightweight sequence model, trained *only* on monocular wrist translation trajectories (discarding rotation and force), predict the physical stability (success/failure) of bi-manual manipulation episodes with accuracy significantly better than a geometry-only baseline?

**Hypothesis**: Translation trajectories implicitly encode sufficient kinematic constraints (e.g., center-of-mass shifts, contact dynamics) to predict stability, even without explicit force or rotational data.

**Null Hypothesis ($H_0$)**: The translation-only model's performance is not significantly better than the geometry-only baseline (p ≥ 0.05 in McNemar's test).

## 2. Dataset Strategy

### Verified Sources & Feasibility

The project **does not** rely on pre-existing external datasets for the primary analysis. Instead, it generates a **synthetic dataset** using the **PyBullet** physics engine. This is a deliberate design choice to satisfy the "Translation-Only" constraint (Constitution Principle VII) and to ensure full control over the ground truth labels (tipping/slippage) which are not available in standard real-world manipulation datasets.

*   **Physics Engine**: PyBullet (CPU-based).
    *   *Source*: PyBullet is an open-source physics engine. No external URL is cited as the "dataset" because the data is generated *in situ*.
    *   *Feasibility*: PyBullet runs natively on CPU and is compatible with the 2-core/7GB RAM constraint.
    *   *Reproducibility*: PyBullet, Euler integration, 1000 steps/sec.
*   **Reference for Physics Validity**: The stability metrics (tipping angle ≥ 15°, slippage ≥ 0.02m) are based on standard rigid-body dynamics principles found in robotics literature (e.g., center-of-mass projection).
    *   *Note*: No specific external dataset URL is needed for the *generation* logic, as the physics engine provides the ground truth.

### Data Generation Strategy (Synthetic)

1.  **Environment**: PyBullet simulation of a bi-manual setup with a rigid object.
2.  **Input**: Randomized initial object poses and random translation trajectories for the end-effectors.
3.  **Dynamic Regime Variation**: To ensure the test set geometries introduce **novel dynamic regimes**, the test set will be generated with randomized mass distributions, friction coefficients, and geometric primitives (e.g., varying aspect ratios, hollow vs. solid) distinct from the training set. This prevents the model from learning only geometric invariance.
4.  **Filtering**: The simulation logs *only* relative wrist translation vectors and initial object bounding box coordinates. Rotation quaternions, joint torques, and force sensor readings are explicitly discarded at the logging stage.
5.  **Labeling**:
    *   **Success (1)**: Tipping angle < 15° AND slippage distance < 0.02m.
    *   **Failure (0)**: Tipping angle ≥ 15° OR slippage distance ≥ 0.02m.
6.  **Volume**: Generate ≥ 5,000 valid episodes.
7.  **Splitting**: A **geometry-disjoint split** is implemented. The dataset is partitioned by unique object geometry IDs. The test set contains *only* geometries not seen in the training set.

### Baseline & Control Strategies

*   **Geometry-Only Baseline**: A model trained *only* on `initial_object_bounds`. To isolate input modality from model capacity, this baseline will be an **MLP with comparable parameter count** (e.g., ~1M-2M params) to the main Transformer, not a simple logistic regression.
*   **Shuffled-Translation Control**: A model trained on translation sequences where the temporal order is shuffled. This breaks the temporal causality, testing if the *sequence* matters vs. just the *set* of points.

## 3. Statistical Methodology

### McNemar's Test

To compare the translation-only model against the geometry-only baseline, we use **McNemar's test**. This is appropriate for comparing two classifiers on the *same* test set (paired nominal data).

*   **Input**: A 2x2 contingency table of predictions (Model A vs. Model B) on the test set.
*   **Metric**: The test statistic follows a $\chi^2$ distribution with 1 degree of freedom.
*   **Significance**: $p < 0.05$ indicates the translation-only model is significantly better.

### Shuffled-Control Comparison

We also perform McNemar's test comparing the **Main Model** against the **Shuffled-Translation Control**. This tests the specific hypothesis that the *temporal sequence* of translation encodes stability, rather than just the set of points.

*   **Null Hypothesis ($H_{0,control}$)**: The main model's performance is not significantly better than the shuffled control (p ≥ 0.05).

### Sensitivity Analysis

To address FR-008, we perform a sensitivity analysis on the labeling thresholds AND physics parameters:
1.  **Threshold Sweep**: Vary tipping angle threshold by ±5% (e.g., 14.25° to 15.75°) and slippage by ±5% (0.019m to 0.021m).
2.  **Physics Sweep**: Vary friction coefficients and mass distribution by ±10% in the simulation.
3.  **Re-labeling & Re-training**: For each sweep point, **re-label the raw dataset** and **re-train (or fine-tune) the models**. This ensures the measured variance reflects model robustness to label definition and physics parameters, not just label consistency.
4.  **Report**: The variance in accuracy across the sweep.

### Power & Multiplicity

*   **Sample Size**: A substantial number of episodes is a synthetic generation target. While not a statistical "power calculation" in the traditional sense (as we control the data volume), this volume is chosen to ensure stable estimates for the McNemar test (expected cell counts > 5).
*   **Multiplicity**: Only one primary hypothesis is tested (Translation vs. Geometry). No family-wise error correction (e.g., Bonferroni) is required beyond the standard $\alpha = 0.05$.

## 4. Compute Feasibility & Architecture

### CPU-First Strategy

The project strictly adheres to the **CPU-Tractability Constraint** (Constitution Principle VI).

*   **Model Architecture**: A lightweight 4-layer Transformer encoder.
    *   *Reference*: Inspired by efficient architectures like **PyramidTNT-Ti** (10M parameters) [source: 2201.00978, https://arxiv.org/abs/2201.00978].
    *   *Parameter Count*: Strictly capped at <10,000,000.
    *   *Precision*: Default floating-point (float32) on CPU.
*   **Training**:
    *   Batch size and sequence length will be tuned to fit within 7GB RAM.
    *   No CUDA, no `bitsandbytes`, no GPU-specific acceleration.
    *   Training time target: < 4 hours (leaving 2 hours for data generation and evaluation).

### GPU Escape Hatch (Not Required)

Given the constraints (<10M params, 5k episodes, CPU physics), a GPU escape hatch is **not** required. The plan assumes the CPU-only form is faithful and sufficient. If the 6-hour limit is exceeded, the plan dictates reducing batch size or sequence length, not switching to a GPU.

## 5. Decision/Rationale & Mitigations

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data (PyBullet)** | Real-world datasets (e.g., ADNI, HCP) are access-gated and lack the specific "translation-only" modality with ground-truth stability labels. Synthetic data ensures reproducibility and strict adherence to the "Translation-Only" constraint. |
| **Geometry-Disjoint Split** | Essential to test generalization to *novel* objects, not just memorization of specific shapes. This aligns with the "Transfer" aspect of the research question. |
| **McNemar's Test** | The most appropriate statistical test for comparing two dependent classifiers (same test set) on binary outcomes. |
| **Lightweight Transformer** | A 4-layer Transformer provides sufficient capacity to learn sequence patterns while staying well under the 10M parameter limit and fitting in 7GB RAM on CPU. |
| **Sensitivity Analysis** | Required to ensure the results are not an artifact of arbitrary threshold choices (15°, 0.02m) or specific physics parameters. |

### Sim-to-Real & Tautology Mitigation

**Risk**: The plan defines the ground-truth label (stability) using physics metrics derived from the *same* PyBullet simulation that generates the translation trajectories. This creates a circular validation: the model is trained to predict a label that is a direct function of the physical state that *caused* the translation. If the physics engine is deterministic, the translation sequence is a sufficient statistic for the label. The analysis risks confirming a tautology (physics consistency) rather than testing if translation *implicitly* encodes stability in a way that generalizes beyond the specific simulation dynamics.

**Mitigation**:
1.  **Geometry-Disjoint Split**: Ensures the model cannot simply memorize the mapping for specific shapes.
2.  **Dynamic Regime Variation**: By varying mass, friction, and geometry primitives in the test set, we ensure the model must learn the *general* relationship between translation and stability, not just the specific dynamics of the training set.
3.  **Physics Parameter Sweep**: The sensitivity analysis varies friction/mass, testing if the model trained on one set of parameters generalizes to another. This is a stronger test of "implicit encoding" than just threshold sweeping.
4.  **Associative Framing**: All results will be framed as associational, acknowledging the simulation-based nature of the data.
