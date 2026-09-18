# Research: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

## Summary of Approach

This research investigates whether the internal activation patterns of the LingBot-Video MoE model encode physical laws. The methodology involves extracting latent vectors and expert masks from the model, generating independent ground-truth labels via 3D reconstruction and *synthetic perturbation*, and training a lightweight classifier to predict physical validity. The study is strictly observational, framing all findings as **associational**. The "ground truth" for the "invalid" class is the *known perturbation logic*, not the depth estimate, breaking the circularity of using depth estimation as a ground truth.

**Note on Causal Claims**: The hypothesis that the model "encodes physical laws" is tested by demonstrating a statistically significant association between internal states and physical validity, *after* rigorously ruling out confounds (e.g., depth estimation artifacts). The classifier performance alone does not prove causality; it provides evidence of encoding.

## Dataset Strategy

The project will utilize the **RoboNet** and **Ego4D** datasets, specifically subsets known to contain robot manipulation videos. These datasets are chosen for their visual fidelity (texture, lighting) which is required for monocular depth estimation to produce plausible trajectories.

| Dataset | Source URL | Loading Method | Variables Needed | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **RoboNet** | `https://huggingface.co/datasets/RoboNet/robonet` | `datasets.load_dataset(..., streaming=True)` | Video frames | Primary source. Filtered by texture score. |
| **Ego4D** | `https://huggingface.co/datasets/Ego4D/ego4d` | `datasets.load_dataset(..., streaming=True)` | Video frames | Supplementary source. Filtered by texture score. |

**Data Availability & Feasibility**:
- The selected datasets are directly downloadable via Hugging Face `datasets` library with streaming enabled, ensuring they can be processed on the CI runner without exceeding disk limits.
- **No access-gated data** is used. All sources are public and open.
- **Visual Fidelity Check**: Clips are filtered based on a pre-computed 'texture score' (variance of pixel intensities) to ensure they contain sufficient visual cues for monocular depth estimation. Clips failing this check are excluded *before* depth estimation.
- **Streaming Strategy**: To handle large datasets within the 7 GB RAM limit, the pipeline will use `streaming=True` to iterate over clips one at a time, processing and saving results immediately without loading the entire dataset into memory.

## Methodological Rigor

### Statistical Rigor (Quantitative Studies)

- **Multiple-Comparison Correction**: If multiple hypotheses are tested (e.g., different expert masks), a Bonferroni correction or False Discovery Rate (FDR) control will be applied to the p-values.
- **Sample-Size / Power Justification**: A 'Power Analysis for Imbalanced Data' is performed. The Minimum Detectable Effect (MDE) is calculated based on an assumed noise floor derived from the depth estimator's reported confidence scores. If the MDE exceeds a reasonable threshold (e.g., Cohen's h > 0.5), the study will report this limitation and not claim a negative result.
- **Causal Inference Assumptions**: The study is **observational**. No causal claims will be made. The correlation between expert activations and physical validity will be framed as associational. The independence of the label generation process (perturbation logic) from the feature extraction process (LingBot) is crucial to avoid circularity.
- **Measurement Validity**: The monocular depth estimator and physics engine (PyBullet) are standard tools in robotics research. Their validity is assumed based on prior literature, but the study will report confidence scores for depth estimation to filter low-quality labels. The "ground truth" is the *perturbation*, not the depth estimate.
- **Predictor Collinearity**: Expert activation masks are likely correlated. The study will report the correlation structure and acknowledge that independent effects cannot be claimed for highly collinear predictors.
- **Label Noise Estimation**: A 'Label Noise Estimation' step calculates the Signal-to-Noise Ratio (SNR) upper bound based on the variance of the depth estimates to quantify the ambiguity of the null result.

### Control Experiments (Addressing Confounds)

To ensure the classifier is not learning artifacts of the labeling pipeline (e.g., depth estimation confidence) rather than physical validity:
1.  **Label Shuffle Control**: The labels ("valid"/"invalid") are randomly shuffled. The classifier should perform at chance level. If it performs well, the model is learning a spurious correlation with the input features unrelated to the label.
2.  **Random Depth Control**: A subset of clips is processed with random noise instead of actual depth maps. The resulting "invalid" labels (based on random physics) should not be predictable from the LingBot features if the features encode real physics.
3.  **Depth Confidence Check**: The `label_independence_score` (correlation between depth confidence and perturbation type) must be < 0.1. A higher score indicates the "invalid" label is correlated with the quality of the depth estimate, not the physical perturbation.

### Computational Feasibility

- **CPU-First**: The entire pipeline (feature extraction, depth estimation, physics simulation, classification) is designed to run on CPU.
- **Memory Management**: Frame subsampling and temporal chunking will be used to ensure processing stays within the 7 GB RAM limit. A 'Verify Memory Chunking' task logs peak RAM usage.
- **GPU Escape Hatch**: If the monocular depth estimation fails on CPU or is too slow, the pipeline may offload this specific step to a Kaggle GPU (scaled down). However, the primary plan assumes CPU execution.
- **Dataset Streaming**: The `datasets` library with `streaming=True` will be used to avoid loading the entire dataset into memory.

## Constitution Check

- **Principle VI (Latent-Space Grounding)**: The plan ensures that the physics engine labels are mechanically decoupled from the LingBot model's internal states. The `prior_audit.py` script and `label_independence_score` metric verify this independence.
- **Principle VII (CPU-Tractable Efficiency)**: The plan prioritizes CPU-tractable methods. The `torch.no_grad()` context and memory chunking are explicitly included. The 'Verify Memory Chunking' task logs peak RAM usage.
- **Principle I (Reproducibility)**: Random seeds are pinned, and all data sources are verified. The pipeline is designed to run end-to-end on a fresh runner.

## Risks & Mitigations

- **Risk**: Monocular depth estimation fails or produces low-confidence outputs.
  - **Mitigation**: Filter out samples with confidence < 0.9 (FR-008). Use a robust depth estimator and log excluded samples. Apply 'Visual Fidelity Check' to filter unusable videos.
- **Risk**: Physics simulation crashes due to numerical instability.
  - **Mitigation**: Catch exceptions, log the clip ID, and exclude the sample from the training set. 'Simulation Stability Check' distinguishes between reconstruction failure and physical violation.
- **Risk**: Dataset lacks sufficient physical violations.
  - **Mitigation**: Use a 'Synthetic Perturbation' strategy to generate the 'invalid' class. Use a 'Control Perturbation' strategy to verify robustness.
- **Risk**: Memory overflow during feature extraction.
  - **Mitigation**: Implement frame subsampling and temporal chunking (FR-006). 'Verify Memory Chunking' task logs peak RAM usage.
- **Risk**: Label noise from depth estimation.
  - **Mitigation**: Calculate 'SNR Upper Bound' and report it. Use 'Perturbation Independence Check' to ensure labels are not correlated with depth confidence.