# Automated-review action items — Qwen-VLA: Unifying Vision-Language-Action Modeling across Tasks, Environments, and Robot Embodiments

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims model 'matches the best' on LIBERO (97.9%), but Table 1 shows ABot-M0 at 98.6%. Clarify that it is second-best or competitive, not the best.
- **[writing]** Section 5.1.2 states the model outperforms pi_0.5 and GR00T, then cites a +35.4pp gain. This gain applies only to pi_0.5 (76.9% vs 41.5%), not GR00T (25.4%). Clarify the specific comparison for the statistic.
- **[writing]** Abstract cites '76.9% average OOD success in real-world ALOHA'. Ensure this is clearly distinguished from simulation OOD results (SimplerEnv, DOMINO) to avoid aggregation confusion.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The diagram contains a large, unexplained block on the far left labeled 'Qwen-VLA' with 'Qwen3.5 VLM' and 'DiT' components that is not referenced in the caption or the Stage I-IV flow, creating confusion about whether this represents the model architecture or an additional training phase.
- **[writing]** Figure 2: The legend defining the symbols (e.g., the flame icon for 'unfrozen' or 'active' modules) is missing from the figure itself and not defined in the caption, making it difficult to interpret the status of the VLM and DiT blocks in Stages II, III, and IV.
- **[science]** Figure 3: The top row caption describes the task as 'Place the two green staplers side by side,' but the visual evidence shows the robot manipulating a blue stapler and a yellow stapler, not two green ones. This contradicts the visual data shown.
- **[science]** Figure 3: The middle row depicts a task involving a 'cake server' (as per the image text), but the caption only describes the top and bottom rows, omitting the middle row entirely.
- **[writing]** Figure 4: The caption 'Task Overview' is too brief to describe the complex content shown, which includes six specific tasks, generalization categories, and visual examples.
- **[writing]** Figure 4: The legend at the top uses color swatches to map to tasks, but the text labels are not aligned with the swatches, making it slightly harder to read.
- **[science]** Figure 4: The figure mixes 'In-Domain Tasks' (center) with 'Generalization' examples (sides) without clearly distinguishing them as separate experimental conditions or categories.
- **[fatal]** Figure 5 caption is truncated mid-sentence at the end of part (b) ('...when pairin'), failing to describe the full experiment shown in the line plot.
- **[science]** Figure 5(b) lacks error bars on the line plot data points, yet the caption implies a comparison of success rates which typically requires uncertainty quantification.
- **[writing]** Figure 6: The caption for panel (c) is truncated ('(c) T2A [t2a_combined.pdf]'), omitting the description of the training duration ablation shown in the plot.
- **[science]** Figure 6: Panel (b) heatmap labels 'SFT: Beta' and 'SFT: Sig-Norm' are swapped relative to the caption's claim that 'Sigmoid-Normal at T2A and Beta at SFT' is optimal; the visual data contradicts the text description.
- **[science]** Figure 7: The caption describes the top-right panels as showing a 'clean up the table' task with sequential pick-and-place into a bin (blue umbrella, toy duck, bottled yogurt), but the images show the robot grasping a green broccoli and a pink bottle, and the bin is empty in the final frame, contradicting the claim of successful sequential placement.
- **[writing]** Figure 7: The caption lists 'blue umbrella' as an object in the top-right task, but the object being manipulated is clearly a blue plush toy or stuffed animal, not an umbrella.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'DiT' (Diffusion Transformer) and 'AdaLN' (Adaptive Layer Normalization) at first use in Section 2.2. Currently, these acronyms appear without expansion, excluding readers unfamiliar with specific diffusion architecture variants.
- **[writing]** Define 'T2A' (Text-to-action) and 'CPT' (Continued pretraining) before using them as standalone labels in Section 3.1 and Figure 2. The text introduces them as bolded phrases but does not explicitly state the acronym mapping for future reference.
- **[writing]** Define 'OSR' (Oracle Success Rate) and 'SR' (Success Rate) in the Abstract and Section 5.1.1. While 'SR' is common, 'OSR' is a specific metric that should be spelled out upon first mention to ensure clarity for non-specialists.
- **[writing]** Define 'OOD' (Out-of-Distribution) at its first appearance in the Abstract. The term is used immediately to describe generalization results without explanation, which may confuse readers from adjacent fields.
- **[writing]** Define 'SDE' (Stochastic Differential Equation) in Section 4.2 when discussing the conversion of the flow-matching ODE. The text assumes the reader knows the mathematical transformation without defining the acronym.
- **[writing]** Define 'GAE' (Generalized Advantage Estimation) in Section 4.2. While PPO is well-known, GAE is a specific component of the algorithm that should be defined for a general audience.
- **[writing]** Define 'SE(3)' in Section 3.1.1 when describing wrist motion. While standard in robotics, it is a mathematical group notation that should be briefly explained (e.g., 'SE(3) rigid body transformations') for broader accessibility.
- **[writing]** Define 'nDTW' (normalized Dynamic Time Warping) in Table 3. The metric is listed in the header without expansion, making it opaque to readers not specializing in navigation evaluation metrics.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that Qwen-VLA unifies 'trajectory prediction' (Intro) is unsupported. Navigation results (Table 3) report standard VLN metrics (OS, SR) but do not evaluate continuous trajectory prediction or motion forecasting, creating a gap between the stated scope and validation.
- **[writing]** The abstract claims 76.9% OOD success on ALOHA, but Table 2 lists 'Position' as an OOD category without defining if this refers to object placement or robot start position. The specific OOD protocol is undefined, making the causal link between the training method and reported generalization ambiguous.
- **[science]** The ablation in Section 5.2.4 discards state conditioning as 'marginal' despite a +1.3pp gain on RoboTwin-Hard. This contradicts the inclusion of RL, which only yields +0.4pp on SimplerOOD (Table 4). The logical justification for discarding a larger effect size is inconsistent.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The abstract and introduction claim Qwen-VLA unifies 'trajectory prediction' and 'driving' (Sec 1, Sec 2.1), yet the experimental section (Sec 5) provides no quantitative results on autonomous driving benchmarks (e.g., nuScenes, Waymo) despite listing driving VQA data in the pretraining mixture. This overstates the model's demonstrated capabilities.
- **[writing]** The claim of '76.9% average OOD success in real-world ALOHA experiments' (Abstract) conflates in-domain and out-of-distribution results. Table 3 shows 83.6% in-domain and 76.9% OOD. The abstract phrasing implies the 76.9% figure applies to the general real-world evaluation, obscuring the distinction between standard and OOD performance.
- **[science]** The paper claims 'strong generalist performance' across 'navigation, manipulation, and egocentric action modeling' (Abstract, Conclusion). However, the navigation results (Table 4) show Qwen-VLA-Instruct trailing StreamVLN in Success Rate (57.5% vs 56.9% is a marginal lead, but SPL is lower) and the egocentric data is only used for pretraining without specific egocentric action benchmarks reported. The 'unified' claim overreaches the specific benchmark evidence.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper incorporates 6.0% egocentric human data (Ego4D, EPIC-KITCHENS, etc.) but lacks a dedicated 'Ethical Considerations' or 'Data Privacy' section. Explicitly state the consent status of these datasets, how PII was handled, and confirm compliance with the original data licenses regarding commercial or research use.
- **[writing]** The model is trained on autonomous driving VQA data (nuScenes, Waymo) and deployed for navigation. A 'Dual-Use' or 'Safety' discussion is missing. Address potential risks of deploying this generalist model in unstructured real-world environments (e.g., unintended physical harm, navigation failures in public spaces) and propose mitigation strategies or deployment constraints.
- **[writing]** The RL stage uses sparse binary rewards in SimplerEnv. Clarify if any safety constraints (e.g., collision avoidance, force limits) were explicitly enforced during the RL rollout or if the model relies solely on the pre-trained policy's implicit safety. If safety constraints were not explicitly modeled, acknowledge this as a limitation for real-world deployment.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations) for the reported success rates in Tables 1, 2, and 3. The current presentation of single-point estimates (e.g., 97.9%, 83.6%) without variance metrics makes it impossible to assess the robustness of the gains over baselines like pi_0.5 or GR00T.
- **[science]** Clarify the sample size (N) and number of random seeds used for the real-world ALOHA experiments (Table 2). The text mentions 'real-world ALOHA experiments' but does not specify if the reported 83.6% average is an aggregate of multiple trials, seeds, or a single run, which is critical for evaluating the reliability of the OOD claims.
- **[science]** Provide a detailed description of the randomization strategy and sample size for the DOMINO dynamic manipulation benchmark (Table 4). The claim of 26.6% zero-shot success is significant; the review requires evidence that this result is not an artifact of a specific seed or a small, non-representative subset of the 35 suites mentioned.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for all success rates (Tables 1-10). Single-point estimates prevent assessing statistical significance of claimed gains (e.g., +2.9pp RL gain).
- **[science]** Clarify the number of independent seeds or trials used for aggregate success rates. The text mentions '128 parallel envs' but does not specify if benchmark scores are averages over multiple seeds, which is critical for variance estimation.
- **[science]** Address the multiple-comparisons problem in ablation studies (Tables 11-14). With many configurations tested, lack of correction (e.g., Bonferroni) risks inflating Type I error rates for claimed 'marginal gains'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (Model Architecture), the phrase 'multi-section RoPE' is used without definition. Define this term or cite the specific method (e.g., YaRN, LongRoPE) to ensure clarity for readers unfamiliar with this specific implementation detail.
- **[writing]** Section 5.1.2 (Real World Manipulation) introduces the model variant notation ${\text{Qwen-VLA-aloha}}_{\text{w/ pretrain}}$. This notation is visually cluttered and inconsistent with standard academic style. Consider renaming the model to 'Qwen-VLA-Aloha-FT' or similar for better readability in text and tables.
- **[writing]** The abstract lists specific performance metrics (e.g., '97.9% on LIBERO') but does not explicitly state the baseline or comparison metric (e.g., 'improvement over SOTA' or 'absolute score'). Clarify whether these are absolute success rates or relative improvements to avoid ambiguity.
