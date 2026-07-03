# Automated-review action items — minWM: A Full-Stack Open-Source Framework for Real-Time Interactive Video World Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.2 (Stage 2 option b), the paper claims causal CD is 'theoretically equivalent' to causal ODE distillation citing Zhao et al. (2026). This equivalence typically holds only under specific assumptions (e.g., linear ODEs or specific noise schedules) which are not stated. The claim should be qualified to avoid implying universal equivalence.
- **[writing]** Table 1 reports a 223.75x speedup for HY1.5. The calculation (771.041 / 3.446) is correct, but the text claims this is a 'reduction' in latency. While colloquially acceptable, 'speedup factor' is the precise term for the ratio, whereas 'reduction' implies a subtraction (e.g., 99.5% reduction). Clarify terminology to ensure precision.
- **[writing]** The paper cites 'li2026cameras' (PRoPE) for camera injection. As this is a 2026 citation, verify that the method described (GTA form injection with block-diagonal projective matrices) is accurately attributed to that specific preprint and not a conflation with other camera-conditioning methods (e.g., ControlNet-style or standard cross-attention).

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The rendered image displays a fantasy landscape with video game UI overlays (WASD keys) rather than the scientific data (e.g., loss curves, sample comparisons) described in the caption regarding 'Training with very small batch sizes' and 'Wan2.1-based model' failure.
- **[fatal]** Figure 2: The rendered image displays a fantasy landscape with game UI overlays (WASD keys) rather than scientific data, charts, or training curves. It fails to visually support the caption's claim about 'Training with estimated camera poses' or 'SpatialVid data'.
- **[science]** Figure 2: The image contains no axes, units, legends, or error bars, making it impossible to evaluate the 'reliable camera-controllable generation' or 'perception-estimated camera poses' mentioned in the caption.
- **[writing]** Figure 3: The figure displays a grid of images with overlaid keyboard controls (WASD, arrows) but lacks a legend or explicit labels defining what specific camera action (e.g., pan, tilt, zoom) corresponds to each column or row.
- **[writing]** Figure 3: The caption states the model supports generation under 'different camera actions' but does not describe the specific actions shown in the grid, making it difficult to verify the claim without guessing based on the icons.
- **[fatal]** Figure 5: The rendered image displays three identical screenshots of a desert landscape with game UI overlays (WASD/arrow keys), which does not visually support the caption's claim about 'early-stage training' or 'camera controllability' failure. There are no axes, data plots, or comparative metrics shown to substantiate the scientific claim.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'MMDiT' at first use in the Abstract and Introduction. While common in diffusion literature, it is an acronym that excludes non-specialist readers without a brief expansion (e.g., 'Mixture-of-Experts Multi-Modal Diffusion Transformer' or similar).
- **[writing]** Define 'DMD' (Distribution Matching Distillation) at first use in the Abstract and Section 3. The term is used as a proper noun without expansion, assuming prior knowledge of the specific distillation technique.
- **[writing]** Define 'PF-ODE' (Probability Flow Ordinary Differential Equation) at first use in Section 3.2. The acronym is used without definition, which may confuse readers unfamiliar with the specific terminology of score-based generative modeling.
- **[writing]** Define 'GTA' (Global Token Attention or similar) in Section 3.1 where the PRoPE injection is described. The text states 'in the GTA form' without explaining what GTA stands for or how it differs from standard attention mechanisms.
- **[writing]** Define 'SE(3)' in Section 3.1. While standard in robotics, explicitly stating 'the special Euclidean group of 3D rigid body transformations' upon first mention improves accessibility for general ML readers.
- **[writing]** Define 'EMA' (Exponential Moving Average) in Section 3.2 when describing the teacher model update. This is a standard optimization term but should be spelled out for clarity in a framework paper.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Sec 3.2 (Stage 3), Eq 4 minimizes KL to p_data, but text claims alignment with the 'bidirectional teacher'. Clarify if s_real approximates p_data or the teacher's distribution to resolve the logical conflict in the training signal source.
- **[writing]** Table 1 compares total bidirectional generation time against AR first-frame time. This 'total vs. partial' comparison logically inflates the speedup metric. Clarify if the baseline should be bidirectional first-frame latency for a fair interactivity comparison.
- **[science]** Sec 4.3 claims WorldPlay-generated trajectories are 'effectively ground-truth' while SpatialVid estimates are noisy. Logically justify why a generative model's conditioned output is superior to perception estimates, as both are synthetic/non-physical.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'real-time' interaction in the title and abstract is not fully supported by the reported latencies. Table 1 shows a first-frame latency of 1.137s for Wan2.1 and 3.446s for HY1.5. While this is a significant speedup, a >1s delay contradicts the standard definition of 'real-time' (typically <100ms or <33ms for 30fps) in interactive systems. The text should temper this claim to 'low-latency' or explicitly define the specific interactive scenario where >1s latency is acceptable.
- **[writing]** The paper claims the framework is 'architecture-extensible' and 'modular' (Abstract, Intro), yet the experimental validation is limited to only two specific backbones (Wan2.1 and HY1.5). There is no evidence provided that the pipeline works on other architectures (e.g., U-Net based models or different MMDiT variants) without significant re-engineering. The claim of general extensibility is an over-extrapolation from the current limited instantiation.
- **[science]** The ablation on 'minimal batch size' (Sec 4.3) claims that batch size 16 is required for 'high controllability' based on visual inspection of Figure 4. However, the paper does not provide a quantitative metric (e.g., pose error, trajectory alignment score) to substantiate the qualitative jump from 'unstable' (BS=8) to 'high controllability' (BS=16). Without quantitative evidence, the specific threshold of 16 is an over-claim based on subjective visual assessment.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes using 'WorldPlay' to generate synthetic training videos from OpenVid images (Sec 4.3). As this involves generating realistic video content from potentially uncurated internet images, the authors must explicitly state the data filtering protocols used to prevent the model from learning from or reproducing harmful, biased, or copyrighted content present in the source images.
- **[writing]** The framework enables 'real-time interactive' video generation with camera control (Abstract, Sec 1). This capability carries dual-use risks for generating deepfakes or disinformation. The manuscript currently lacks a dedicated 'Ethical Considerations' or 'Limitations' section discussing potential misuse, mitigation strategies (e.g., watermarking), and responsible release guidelines for the open-source code.
- **[writing]** The ablation study in Sec 4.3 notes that models trained on 'SpatialVid' (perception-estimated poses) failed, while those trained on 'DL3DV' (reconstructed scenes) succeeded. The authors should clarify the provenance and consent status of the DL3DV dataset, specifically whether the 3D reconstructions were performed on data with appropriate usage rights for training generative models.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation studies on training steps (Sec 4.3, Fig. ablation-steps) and batch size (Sec 4.3, Fig. ablation-bs) rely entirely on qualitative visual inspection of generated frames. To support the claim of 'strong controllability' or 'failure to learn,' quantitative metrics (e.g., camera pose error RMSE, trajectory alignment scores) or statistical significance tests across multiple seeds are required to rule out cherry-picking.
- **[science]** The latency claims in Table 1 (Sec 4.1) report single-run measurements on a single A800 GPU without reporting variance, standard deviation, or confidence intervals. Given the stochastic nature of GPU scheduling and memory allocation, a single measurement is insufficient to substantiate the precise speedup factors (e.g., 236.64x) claimed.
- **[science]** The paper claims the framework is 'architecture-general' by instantiating it on Wan2.1 and HY1.5 (Sec 1, Sec 4). However, the experimental evidence is limited to these two specific models. To robustly support the generalization claim, the authors should either include a third distinct architecture or explicitly qualify the claim to the tested architectures.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The ablation studies on training steps (Sec 4.3, Fig. 3) and batch size (Sec 4.3, Fig. 4) rely entirely on qualitative visual inspection. To support the claim of 'strong controllability' or 'instability,' report quantitative metrics (e.g., camera pose error RMSE, trajectory alignment scores) with confidence intervals or standard deviations across multiple seeds.
- **[science]** Latency results in Table 1 are reported as single point estimates without variance. Given the stochastic nature of GPU inference and potential system noise, report mean latency and standard deviation over multiple runs to validate the claimed speedup factors.
- **[science]** The claim that batch size < 4 'often fails' (Sec 4.3) lacks statistical definition. Specify the failure rate (e.g., 0/5 seeds failed) and the criteria used to define 'failure' to ensure reproducibility of the threshold.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (Method), the first sentence of the main paragraph lacks a space after the period: '...video generator.The pipeline...'. This is a clear typographical error that disrupts readability and should be corrected.
- **[writing]** In Section 3.2, the enumeration of the three distillation stages is formatted awkwardly within the text: '...three stages: mph{	extbf{(1) Stage 1... (3) Stage 3: asymmetric DMD.}}'. The use of bolding and italics for the list items within a running sentence is visually cluttered. Consider simplifying to '...three stages: (1) AR diffusion training; (2) causal ODE or causal CD initialization; and (3) asymmetric DMD.'
- **[writing]** In Section 4.2 (Results), the paragraph heading 'Few-step AR models substantially reduce the first-frame latency.' ends with a period, but the subsequent text begins immediately on the same line without a line break or proper paragraph separation in the source, causing a formatting glitch in the compiled PDF where the text runs into the heading. Ensure proper paragraph breaks are used.
