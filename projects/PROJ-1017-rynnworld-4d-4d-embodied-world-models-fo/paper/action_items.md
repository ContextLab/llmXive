# Automated-review action items — RynnWorld-4D: 4D Embodied World Models for Robotic Manipulation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** The paper contains several critical factual inaccuracies regarding hardware, software versions, and data interpretation that undermine the validity of its central claims. First, the hardware specification in Table 1 and Section 4.3 cites an "NVIDIA RTX 5090" GPU. As of the current date, this product does not exist in the public domain; the current flagship is the RTX 4090. Since the latency benchmarks (1.1s total cycle) are the primary evidence for the "real-time" feasibility of the system, the

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error ('generates RGB...') missing the subject (e.g., 'the model' or 'RynnWorld-4D'), making it unclear what performs the action.
- **[writing]** Figure 1: The caption includes a citation placeholder '[teasor.pdf]' which should be removed or replaced with the proper citation format.
- **[writing]** Figure 2: The title 'Rynn4DDataset 1.0' and the bottom legend bar are cut off at the bottom edge of the image, making the full legend and total frame count illegible.
- **[writing]** Figure 2: The text labels for the 'Human demonstration videos' pie chart (e.g., 'EgoVid', 'Epic-Kitchens') are extremely small and blurry, reducing readability.
- **[writing]** Figure 3: The text 'Rynn4DDataset 1.0' is superimposed directly over the grid of sample images, significantly reducing the legibility of the underlying visual content.
- **[writing]** Figure 3: The text inside the vertical annotation boxes ('Video captioning', 'Flow annotation', 'Depth annotation') is rotated 90 degrees, making it difficult to read compared to standard horizontal text.
- **[fatal]** Figure 4: The caption contains multiple missing model names (e.g., 'Overview of .', 'co-generates', 'aggregated by -Policy'), rendering the text description incomplete and unprofessional.
- **[science]** Figure 4: The diagram shows 'RynnWorld-4D Block' and 'RynnWorld-4D-Policy' as distinct components, but the caption fails to name the generative model, making it impossible to verify if the visual architecture matches the described system.
- **[writing]** Figure 4: The text 'RynnWorld-4D Block' and 'RynnWorld-4D-Policy' are used in the diagram, but the caption does not define these terms or explain their relationship to the overall pipeline.
- **[writing]** Figure 6: The caption contains a grammatical error and missing subject ('Qualitative results of . Starting from...'), likely due to a missing model name placeholder.
- **[writing]** Figure 6: The caption claims to show 'RGB video, depth maps, and optical flow', but the figure displays four columns per task (RGB, Depth, Flow, and a fourth unlabelled column) without explicitly defining the fourth column in the text.
- **[writing]** Figure 8: The caption 'Operator to collect real world data' is grammatically incomplete and lacks context; it should describe the operator's role or the specific data collection setup shown.
- **[science]** Figure 8: The image contains a large, opaque smiley-face graphic obscuring the operator's head and upper torso, which prevents verification of the operator's identity, safety gear, or interaction with the equipment.
- **[writing]** Figure 9: The caption contains a grammatical error ('highlight 's ability') where the model name is missing.
- **[science]** Figure 9: The figure displays only RGB and optical flow sequences but lacks the depth maps explicitly promised in the caption ('Each row displays the generated RGB, depth, and optical flow sequences').

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1 (Eq. 1) introduces the symbol $	au$ in the phrase 'masking out pixels where $\|
abla D\| > 	au$' without defining it. A competent reader cannot determine the threshold value or its units. Define $	au$ explicitly (e.g., 'where $	au$ is a depth-gradient threshold set to 0.1').
- **[writing]** Section 3.2 introduces the term '3D RoPE' (3D Rotary Positional Embeddings) without expansion or a brief gloss. While 'RoPE' is common in NLP, the '3D' variant (spatial + temporal) is specific to this architecture. Expand at first use: '3D Rotary Positional Embeddings (3D RoPE), which inject spatial and temporal position information'.
- **[writing]** Section 3.2 (Eq. 3) uses the notation $m{K}_l^{	ext{cross}}$ and $m{V}_l^{	ext{cross}}$ without explicitly defining the concatenation operation or the set of indices $j 
eq m$ in the immediate text. While the equation implies it, a reader might miss that 'cross' refers to the concatenation of the *other two* modalities. Add a clause: 'where $m{K}_l^{	ext{cross}}$ is the concatenation of keys from the two complementary modalities ($j 
eq m$)'.
- **[writing]** Section 4.1 (Implementation Details) uses the abbreviation 'bb.' in 'joint (frozen bb.)' in Table 1. This is in-group shorthand for 'backbone' and is undefined. Expand to 'joint (frozen backbone)' for clarity.
- **[writing]** Section 4.2 (Setups and Baselines) lists metrics 'IQ, MS, SC, Subj.' without defining them in the main text, referring readers to the Appendix. While the Appendix defines them, the main text should briefly expand these acronyms at first mention (e.g., 'Imaging Quality (IQ), Motion Smoothness (MS), Subject Consistency (SC), and I2V-Subject (Subj.)') to allow immediate comprehension without page-flipping.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.1 claims 50 Hz execution during a 1.1s cycle for 10 actions, which mathematically implies ~9 Hz. Clarify if 50 Hz refers to the low-level servo holding a static command, as the numbers 9 Hz, 50 Hz, and 1.1s are currently inconsistent.
- **[writing]** The Abstract claims 'high-frequency' control, but Section 3.4 and Conclusion admit a 9 Hz limit. This contradicts standard robotics definitions of high-frequency (>50Hz). Qualify 'high-frequency' in the Abstract to align with the 9 Hz finding.
- **[science]** Section 3.2 clips depth to [0, 5.0]m, yet Section 3.3 claims 'metric scene flow' for 'physically plausible' 3D movements. If scenes exceed 5m, clipping flattens geometry, invalidating the metric claim. Explain how this constraint affects 3D validity in large scenes.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims the method 'solves' the gap between world prediction and policy learning. Section 4 shows a 34% relative improvement on specific bimanual tasks (Hand-over, Lid Placement) but fails on others (e.g., Block Pushing is 97.14% vs 100% baseline). Replace 'solves' with 'significantly narrows' and scope the claim to the tested manipulation tasks.
- **[writing]** Abstract states the model achieves 'state-of-the-art performance' on 'real-world dexterous bimanual manipulation tasks.' Table 2 shows SOTA only on 4 of 6 tasks (Hand-over, Lid Placement, Bowl Stacking, Bimanual Lifting) and is outperformed by pi_0.5 on Block Pushing (100% vs 97.14%). Qualify the claim to 'on tasks requiring high spatial precision' or list the specific tasks where SOTA was achieved.
- **[writing]** Conclusion states the framework 'shifts the paradigm' from 2D to 4D. While the results show improvement, the evidence is limited to a single robot platform (TIANJI M6) and six specific tasks. The claim of a paradigm shift implies a broader field-wide impact not yet demonstrated. Rephrase to 'demonstrates a promising shift' or 'offers a new paradigm for' to reflect the preliminary nature of the evidence.
- **[writing]** The 'Limitation' section admits the model is 'primarily optimized for egocentric perspectives' but the Introduction and Abstract imply general applicability to 'open world' and 'complex 3D world' interactions. The paper does not test multi-view or non-egocentric scenarios. Explicitly state in the Abstract that the current validation is restricted to egocentric views to prevent overgeneralization.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a generative world model for robotic manipulation and a large-scale dataset (Rynn4DDataset 1.0) derived from public sources. From a safety and ethics perspective, the work is low-risk.

The dataset construction relies on publicly available video datasets (e.g., Epic-Kitchens, EgoVid, RoboMIND) and applies automated pseudo-labeling (depth, flow, captions) using existing models. The paper does not claim to release raw, unprocessed video containing Personally Identifiable Information (PII) or sensitive human data; rather, it releases the processed dataset or the pipeline to generate it. While the source videos may contain human faces or activities, the paper does not describe a novel method for re-identifying individuals or scraping data in violation of Terms of Service (ToS) beyond standard academic usage of public benchmarks. The authors cite the source datasets, implying adherence to their respective licenses.

The proposed system (RynnWorld-4D and RynnWorld-4D-Policy) is designed for physical robotic manipulation in controlled or semi-controlled environments. It does not introduce dual-use capabilities for surveillance, deception, or cyber-attacks. The "world model" aspect predicts physical dynamics (RGB, depth, flow) to aid robot control, which is a standard and benign application in embodied AI. There is no evidence of human-subjects research requiring IRB approval, as the data is secondary use of public datasets and the robot experiments involve teleoperation by the authors (standard engineering practice) rather than behavioral studies on human subjects.

No specific, non-trivial risks of harm are identified that are unaddressed in the text. The paper does not require additional safety disclosures or mitigations beyond standard academic practice for this subfield.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper presents a compelling architecture for 4D world modeling, but the experimental design contains several gaps that prevent the results from definitively supporting the strength of the claims made. First, the ablation studies in Table 2 (World Modeling) and Table 3 (Policy Learning) rely on single-point estimates without reporting variance. For instance, the improvement in geometric accuracy (δ1) when adding Modality Adaptation is 0.131 (0.610 vs 0.479). In generative modeling, where resu

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 2 reports success rates (e.g., 94.29%) for 6 tasks based on 35 trials each, but provides no uncertainty metrics (SD, SE, or 95% CI). With N=35, the standard error for a 94% rate is ~3.5%, making the difference between 94.29% and 91.43% statistically indistinguishable without a formal test. Report mean ± SD or 95% CIs for all success rates and clarify if the bolding implies statistical significance.
- **[writing]** Table 1 compares the proposed method against 4 baselines across 10 metrics (40 pairwise comparisons) and highlights 'best' values in bold without any multiple-comparison correction (e.g., Bonferroni or FDR). At α=0.05, ~2 false positives are expected by chance. Apply a correction across the 40 tests or explicitly state that the bolding is for visual ranking only, not statistical significance.
- **[writing]** Section 4.2 claims the method is 'significantly outperforming' baselines in specific tasks (e.g., Lid Placement) but cites no p-values, effect sizes, or statistical tests (e.g., Fisher's exact test or chi-square for success rates). Replace 'significantly' with 'numerically higher' unless a formal hypothesis test with p-values is added to the text or appendix.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 3.1: The paragraph on 'Video captioning' opens with a prompt block that interrupts the narrative flow. The sentence 'For each segment, we provide the following prompt to the model:' is followed immediately by a quote block, leaving the reader hanging. Integrate the prompt description into the sentence or move the block to a figure caption to maintain prose continuity.
- **[writing]** Section 3.2: The paragraph on 'Metric Scene Flow Derivation' contains a sentence ('A 3D point P_t is tracked to its position at t+1 by:') that introduces an equation but lacks a clear subject-verb connection to the preceding context. The transition from the previous sentence about 'temporal correspondences' to the specific tracking formula is abrupt. Add a bridging phrase like 'Specifically, we track a point by...' to clarify the logical step.
- **[writing]** Section 3.3: The 'Phased Training Strategy' subsection lists three stages but the transition between Stage 2 and Stage 3 descriptions is abrupt. The sentence 'With the joint module already aligned, we unfreeze the entire model...' assumes the reader remembers the specific alignment mechanism from Stage 2. Add a brief reference to the 'Joint Cross-Modal Attention' modules to reinforce the continuity of the argument.
- **[writing]** Section 3.4: The 'Action Generation' paragraph ends with a reference to 'Sec.~ef{appendix:latency}' for details on parallel action chunking, but the latency section (3.5) is titled 'Inference Latency and Real-time Control' and focuses on timing breakdown rather than the chunking mechanism itself. The reader must hunt for the chunking explanation. Either rename the section to include 'Action Chunking' or move the chunking explanation to the 'Action Generation' paragraph.
- **[writing]** Section 4.2: The 'Robot tasks' list item (6) 'Bowl Stacking' starts with 'There are two small bowls on the table...', which is a narrative description rather than a task definition. The other items use imperative or descriptive task structures (e.g., 'The robot uses...', 'A sequential pushing task...'). Rewrite this item to match the consistent task-definition style of the other list items.
