# Automated-review action items — PhysisForcing: Physics Reinforced World Simulator for Robotic Manipulation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify the '22.3%' improvement claim in the Abstract and Intro. Table 1 shows a relative increase (11.3/50.7), but the phrasing is ambiguous and could be misread as an absolute percentage point gain. Specify 'relative improvement' for precision.
- **[writing]** In Section 4.2, the claim that PF-Cosmos surpasses Abot-PhysWorld (84.9) with 85.2 implies a larger margin than the actual 0.26 point difference shown in Appendix Table 2. Use exact values or qualify the margin to avoid overstating the lead.
- **[writing]** The claim 'surpassing all baselines' in the Abstract is technically true for listed models but risks overgeneralization. Qualify as 'surpassing all evaluated baselines' to strictly align with the provided Table 1 data scope.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption states that 'WorldArena results use the Wan2.2-TI2V-5B world model trained with PhysisForcing,' but the WorldArena chart in panel (c) labels the method as 'PhysisForcing' rather than 'PF-Wan' or 'PF-Wan2.2' to match the naming convention used for 'PF-Cosmos' in the other charts.
- **[writing]** Figure 1: The caption defines 'PF-Cosmos' for the R-Bench, PAI-Bench, and EZS-Bench charts, but does not explicitly define the label 'PhysisForcing' used in the WorldArena chart, creating a minor inconsistency in nomenclature.
- **[writing]** Figure 2: The legend in the top-right corner defines 'Video tokens' as a white square with a black border, but the diagram uses solid white squares (e.g., in the 'PhysisForcing' box) without borders, creating ambiguity between defined tokens and generic UI elements.
- **[writing]** Figure 2: The 'PhysisForcing' box contains icons for 'Low-level physics' (sine wave) and 'High-level physics' (brain) but lacks a corresponding legend entry to explicitly define these symbols.
- **[science]** Figure 3: The x-axis labels 'PF-Wan' and 'PF-Cosmos' are not defined in the caption, which only defines 'PF-Cosmos' as 'Cosmos3-Nano trained with PhysisForcing' in the context of Figure 1. The caption for Figure 3 fails to explain what 'PF-Wan' represents or how the 'PF-' prefix relates to the baselines.
- **[writing]** Figure 3: The x-axis labels are rotated at a steep angle, making them difficult to read and cluttering the bottom of the chart. A horizontal layout or reduced font size would improve legibility.
- **[science]** Figure 4: The prompt specifies moving the apple onto the 'second-level wooden platform,' but the visual sequence for the proposed method (PF-Cosmos, bottom row) shows the robot failing to grasp or move the apple, leaving it on the table. This contradicts the caption's claim that the method produces 'more physically plausible' interactions for this specific task.
- **[science]** Figure 4: The 'Seedance 1.5 Pro' row depicts the robot successfully grasping and lifting the apple, yet the caption implies this model fails to produce physically plausible interactions compared to the proposed method. The visual evidence in this row does not support the qualitative comparison made in the text.
- **[writing]** Figure 5: The figure has no caption provided ('(no caption)'), making it impossible to verify what the plotted lines represent or what the specific metrics are without guessing.
- **[science]** Figure 5: The legend uses mathematical notation ($\mathcal{L}_{pix}^{phy}$, etc.) that is not defined in the figure or its missing caption, leaving the reader to guess the specific ablation components.
- **[science]** Figure 5: The plot shows a performance drop at 30k steps for all methods, but without error bars or a description of the experimental setup (e.g., number of seeds), it is unclear if this is a significant trend or noise.
- **[writing]** Figure 6: The caption 'Comparison with the state-of-the-art models' is generic and fails to specify the prompt, task, or specific models shown, unlike Figure 4 which details the prompt and method names.
- **[writing]** Figure 6: The image lacks row labels (e.g., model names) to identify which method corresponds to each row, requiring the reader to guess or cross-reference other figures.
- **[science]** Figure 7: The caption states 'Comparison with the state-of-the-art models' but does not identify which models correspond to the rows (e.g., Wan 2.6, Seedance 1.5 Pro, etc.) or define the green border around the bottom row, making the comparison impossible to interpret without external context.
- **[writing]** Figure 7: The caption is identical to those of Figures 6, 8, 9, and 10, providing no unique information to distinguish this specific qualitative comparison from others in the appendix.
- **[science]** Figure 8: The caption states 'Comparison with the state-of-the-art models' but does not identify which models correspond to the rows shown, unlike Figure 4 which explicitly lists them. Without this mapping, the comparison is uninterpretable.
- **[writing]** Figure 8: The caption is identical to Figures 6, 7, 9, and 10, providing no specific context or prompt for the visual content shown, making it impossible to assess if the results match the intended task.
- **[science]** Figure 9: The caption states this is a comparison with state-of-the-art models, but the image contains no text labels identifying which row corresponds to which model (e.g., Wan 2.6, Seedance 1.5 Pro, etc.), making it impossible to distinguish the baselines from the proposed method without external context.
- **[writing]** Figure 9: The caption is generic ('Comparison with the state-of-the-art models') and fails to describe the specific task shown (dual robotic arms capping a pen) or the specific models being compared, unlike Figure 4 which provides these details.
- **[science]** Figure 10: The caption states 'Comparison with the state-of-the-art models' but does not identify which specific models correspond to the rows shown, making the comparison uninterpretable.
- **[writing]** Figure 10: The image filename [Qual_Appx_6.jpg] suggests this is an appendix figure, yet the caption provides no context about what task or prompt is being demonstrated.
- **[writing]** Figure 11: The caption states 'finetuned baseline (top)', but the top row is labeled 'Wan2.2-A14B (ft)' while the bottom row is labeled 'PF-Wan'. The caption should explicitly state that the top row is the finetuned baseline to match the visual labels.
- **[writing]** Figure 11: The caption describes the bottom row as 'PF-Wan (bottom, green)', but the green border is applied to the entire row of images, not just the text or a specific element. This phrasing is slightly ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'DiT' (Diffusion Transformer) at its first occurrence in the Abstract or Introduction. Currently, it appears as 'DiT features' without prior definition, which excludes readers unfamiliar with this specific architecture acronym.
- **[writing]** Replace the term 'physics-informative regions' with a plainer alternative like 'physically active regions' or 'interaction-critical areas' in Section 3.1. The current phrasing is slightly redundant and could be simplified for broader accessibility.
- **[writing]** Define 'MLP' (Multi-Layer Perceptron) at its first use in Section 3.2. While common in deep learning, the paper aims for broad accessibility, and defining standard acronyms at first use is a best practice for non-specialist readers.
- **[writing]** Clarify the term 'flow matching' in Section 3.4. While 'flow matching loss' is used, a brief parenthetical explanation (e.g., 'a generative training objective') would help readers from non-generative-model backgrounds understand the context.
- **[writing]** Replace 'backbone' with 'base model' or 'underlying architecture' in Section 4.1. 'Backbone' is standard jargon in computer vision but may be opaque to general robotics or AI researchers not specialized in model architectures.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.1 (Eq. 2), the foreground weight is defined as r_i = 1/(D_0 + epsilon). Since D_0 is a depth map where larger values indicate objects further away, this formula assigns higher weights to background (far) regions, contradicting the text's claim that it weights 'foreground areas'. The formula should likely be D_0 / (D_0 + epsilon) or similar to prioritize near objects.
- **[science]** In Section 4.2 (Policy Learning), the paper claims PhysisForcing improves downstream policy success. However, Table 1 (RoboTwin results) shows the method degrades performance on 'shake_bottle' (-3.0%) and 'stack_bowls_two' (-6.5%). The text attributes gains to 'contact-rich' tasks but fails to logically reconcile why the proposed physics alignment would harm performance on tasks that arguably also involve physical contact and manipulation, suggesting a missing analysis of failure modes.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that PhysisForcing 'yields stronger representations for robotic manipulation' (Abstract, Conclusion) is over-extended. The policy improvement (Table 1) is marginal (+4.6% avg) and inconsistent (decreases on 3/6 tasks). The paper does not provide ablation evidence isolating whether the gain comes from 'stronger representations' or simply better video fidelity, nor does it rule out that the gains are specific to the Fast-WAM architecture rather than a general property of the video model.
- **[writing]** The assertion that the method 'surpasses all world-model planners' (Abstract, Sec 4.2) is an over-claim. Table 2 shows PhysisForcing (24.0%) beats WoW (20.5%) and TesserAct (18.0%), but TesserAct achieves 35.0% on Task 2. The paper frames the average as the sole metric of superiority without addressing the variance or the fact that TesserAct outperforms the proposed method on a specific task, suggesting the 'surpassing' claim is too absolute.
- **[writing]** The paper claims the method 'consistently improves embodied video generation' (Abstract) and 'improves every backbone' (Sec 4.2). However, Table 1 shows that for the Wan2.2-TI2V-5B backbone, the 'Quadruped' embodiment score drops from 59.0 (base) to 59.7 (ft) to 59.7 (PF), showing negligible or no improvement compared to the significant gains in other categories. The word 'consistently' implies uniform improvement across all dimensions, which the data does not fully support.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader impacts' section (Appendix A.6) acknowledges risks of deceptive footage and synthetic policy training but lacks concrete mitigation strategies beyond 'research-only release.' Explicitly detail technical safeguards (e.g., invisible watermarking, provenance metadata injection) or usage restrictions planned for the code release to address dual-use concerns.
- **[writing]** The training data (RoVid-X, 4M clips) is described as a 'filtered subset' but lacks details on consent, privacy, or ethical sourcing of the underlying robotic videos. Clarify if the dataset contains human operators or private environments and confirm compliance with data privacy standards (e.g., IRB approval or public license verification) to prevent potential privacy violations.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The pixel-level loss (Eq. 9) uses CoTracker3 trajectories as ground truth. Since CoTracker3 has errors on occlusions, the model may learn tracker artifacts. Quantify tracker noise or ablate with a physics-simulated reference to prove gains reflect true physics.
- **[science]** The semantic loss (Eq. 12) aligns with V-JEPA 2, which is not explicitly trained on physical laws. Prove the encoder's relational matrix encodes physical constraints (e.g., contact persistence) via qualitative examples or a control experiment with a non-physical encoder.
- **[science]** Policy results (Table 2) show performance drops on 'shake_bottle' (-3.0%) and 'stack_bowls_two' (-6.5%). Analyze why physics alignment degrades these specific tasks and discuss trade-offs or hyperparameter sensitivity to ensure robustness across the full task distribution.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report uncertainty metrics (e.g., standard deviation or 95% confidence intervals) for all benchmark scores in Tables 1, 2, and 3. The current presentation of single-point averages (e.g., 63.8, 85.2) obscures the variance across the 650 R-Bench prompts or 200 policy rollouts, making it impossible to assess statistical significance of the reported gains.
- **[science]** Clarify the statistical test used to validate the improvements in Table 4 (RoboTwin) and Table 5 (WorldArena). Specifically, state whether the reported success rate differences (e.g., +4.6% average) are statistically significant (p < 0.05) given the sample size (200 rollouts/task) and the observed variance in the baseline performance.
- **[science]** In Section 3.1 (Eq. 3), the adaptive threshold for the physics mask is defined as the mean score. Justify this choice statistically or provide an ablation on the sensitivity of the final results to this threshold (e.g., using median or top-k percentile) to ensure the region selection is robust and not an artifact of the specific thresholding method.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction (Section 1, paragraph 4), the sentence 'Applying supervision uniformly over all pixels dilutes these signals and weakens alignment' is slightly ambiguous. Clarify whether 'these signals' refers to the physical supervision signals or the physical evidence mentioned in the previous sentence to improve logical flow.
- **[writing]** In Section 3.1 (Eq. 4), the notation uses \lfloor \cdot \rceil for rounding. While defined in the text, the symbol \rceil is non-standard for rounding (usually \lfloor \cdot \rfloor or \lfloor \cdot \rceil is not a standard pair). Consider using standard notation or explicitly defining the rounding operator to avoid confusion for readers unfamiliar with this specific LaTeX macro.
- **[writing]** In Section 4 (Table 1 caption), the phrase 'Per-column rankings are highlighted in...' is followed by color box commands. Ensure the text explicitly states that the colors correspond to 1st, 2nd, and 3rd place to ensure accessibility for readers who may not see the colors or if the PDF is printed in grayscale.
