# Automated-review action items — MolmoMotion: Forecasting Point Trajectories in 3D with Language Instruction

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** In Section 3 (Method), the paper claims ViPE produces 'more accurate 3D trajectories than current end-to-end 3D point trackers such as SpatialTrackerV2' based on an 'empirical' finding. However, no quantitative comparison, ablation study, or citation to a specific benchmark result is provided in the text or appendix to substantiate this superiority claim. This assertion requires evidence or rephrasing to 'we observed' without claiming general superiority.
- **[writing]** The abstract and Introduction claim MolmoMotion 'significantly outperforms all existing motion prediction baselines.' Table 1 shows the AR variant outperforms baselines on most metrics, but the Flow-Matching (FM) variant has higher ADE/FDE than ObjectForesight on the HOT3D subset (0.183 vs 0.129 ADE). The claim of 'significant' outperformance for the *entire* model family is slightly overstated given the FM variant's mixed results on specific subsets compared to rigid-object baselines.
- **[writing]** Section 4 claims the model 'improves training efficiency' in robotics, citing a jump from 19% to 51% success at 10K steps. While the data supports a faster rise, the claim implies a general efficiency gain. The text does not explicitly rule out that the baseline might eventually reach the same plateau with more steps, though the final gap (56% vs 76%) supports the claim. However, the phrasing 'improves training efficiency' is acceptable but could be more precise as 'accelerates convergence'.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Predicted Future 3D Point Trajectory' panel shows a colorbar labeled 'Time' with a gradient from light to dark, but the caption does not define what the colors represent or confirm that the gradient maps to time steps, creating ambiguity in interpreting the trajectory evolution.
- **[writing]** Figure 1: The 'Action' input is described as 'pour water from the tan flask into the red can', but the RGB Observation image shows a white pitcher and a red can — no tan flask is visible, creating a mismatch between the textual instruction and the visual input shown.
- **[writing]** Figure 2: The caption contains a likely citation artifact ('Molmo2 clark2026molmo2') that should be cleaned up for readability.
- **[writing]** Figure 2: The 'Action' input block in the diagram is not explicitly mentioned in the caption's list of shared inputs, though it is visually present.
- **[writing]** Figure 3: The colorbar at the bottom lacks a label or legend entry defining what the color gradient represents (e.g., time, confidence, or velocity), making the visualization ambiguous.
- **[writing]** Figure 3: The graph in the bottom right corner uses the symbol '|Δ3D|' on the y-axis without defining it in the caption or axis label, leaving the metric's physical meaning unclear.
- **[writing]** Figure 4: The caption 'MolmoMotion-1M (pretrain)' is insufficient; it fails to describe the chart's content (distribution of motion verbs) or explain the log-scale y-axis.
- **[science]** Figure 4: The y-axis is labeled '# Clips (log)' with a single tick at 10^4, but lacks a zero baseline or lower bound, making the relative magnitude of the bars difficult to interpret accurately.
- **[writing]** Figure 5: The caption 'MolmoMotion-1M (pretrain)' is too generic and does not describe the bar chart's content (object category distribution) or the y-axis metric ('# Clips (log)'); it should explicitly state that the figure shows the frequency distribution of object categories in the pretraining dataset.
- **[science]** Figure 5: The y-axis is labeled '# Clips (log)' but lacks tick marks or gridlines for values other than 10^4, making it impossible to estimate the magnitude of the bars or the relative differences between categories.
- **[writing]** Figure 6: The caption 'predicts accurate motion trajectories...' lacks a subject (e.g., 'MolmoMotion') and is grammatically incomplete.
- **[writing]** Figure 6: The top-left legend labels 'Prediction' and 'GT' are not defined in the caption, leaving the color mapping for the trajectory lines ambiguous.
- **[science]** Figure 7: The caption describes a 'Pick-and-place task' but the figure displays quantitative performance metrics (Test success rate, Final success rate) without any visual depiction of the task, the environment, or the robot, making it impossible to verify the claim visually.
- **[writing]** Figure 7: The caption is insufficient as it fails to define the evaluation splits (SS, SU, US, UU) shown on the x-axis of the right panel or explain the specific metrics being compared.
- **[writing]** Figure 8 caption contains a sentence fragment ('can plan accurate object trajectories...') lacking a subject, likely due to a copy-paste error.
- **[writing]** Figure 8 caption uses lowercase 'trajectory' in the title line instead of the capitalized 'Trajectory' used in other figure titles (e.g., Figure 2, 7).
- **[writing]** Figure 9 caption contains a grammatical error and missing subject: '-guided videos exhibit...' should specify the model name (e.g., 'MolmoMotion-guided videos').
- **[science]** Figure 9 lacks a legend or row labels identifying the competing methods (e.g., 'Wan2.2-I2V-A14B', 'CogVid-5B-I2V', 'DAS + MolmoMotion'), making it impossible to determine which row corresponds to the claimed 'more physically plausible' results.
- **[science]** Figure 10: The caption claims to show 'predictions on held-out DROID clips,' but the image contains no quantitative data, error bars, or ground-truth comparisons to validate the prediction accuracy.
- **[writing]** Figure 10: The image consists of nine unlabelled sub-panels with no axes, units, or legends, making it impossible to interpret the specific content or metrics shown.
- **[science]** Figure 11: The figure displays qualitative video generation results for prompts 'little pigs walks to the big pig' and 'a giant panda holds a bamboo stick and scratches its head', but the caption 'Video generation comparisons on held-out prompts (1/2)' is generic and does not describe the specific content or the models being compared (Wan2.2, CogVid, MolmoMotion).
- **[writing]** Figure 11: The row labels 'D_A S + MolmoMotion' are vertically compressed and difficult to read; the spacing should be increased for clarity.
- **[science]** Figure 12: The figure displays qualitative video generation results but lacks any labels, legends, or text identifying which specific model (e.g., MolmoMotion vs. baselines) generated each row or column, making the comparison impossible to interpret.
- **[writing]** Figure 12: The caption 'Video generation comparisons on held-out prompts (2/2)' is generic and fails to describe the specific prompts used or the models being compared, which are not visible in the image itself.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that creates a barrier for non-specialist readers. While the technical precision is high, the density of unexplained acronyms and field-specific jargon violates the principle of accessibility. In the Abstract, the term "flow-matching" is introduced without definition. This is a specific generative modeling technique; replacing it with a plain description like "modeling trajectory distributions via velocity fields" would improve clarity. Si

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that 3D points are 'view-stable' (Sec 1) contradicts the methodology in Sec 3.1, which anchors the world frame to the camera at t0. If the camera moves, coordinates change. Clarify if 'view-stable' refers to relative motion or if the frame is truly global (e.g., via SLAM).
- **[writing]** The claim of outperforming 'all' baselines (Abstract, Sec 4) is logically weakened by excluding PointWorld and MotionForcast from Table 1 due to unreleased code. Qualify the claim to 'all evaluated baselines' to avoid overgeneralization.
- **[science]** The dense annotation pipeline (100 points) vs. sparse model input (8 points) lacks logical justification. Explain how dense filtering contributes to training if the model only sees 8 points, or if the pipeline is merely for data generation without direct model impact.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that the model 'significantly outperforms all existing motion prediction baselines' (Abstract, Intro) is overreaching. Table 1 shows ObjectForesight achieves lower ADE (0.129) than MolmoMotion-FM (0.183) on HOT3D with 1-frame input. The claim should be qualified to exclude methods with specific input requirements (e.g., mesh inputs) or to specify the exact conditions under which the outperformance holds.
- **[science]** The assertion that the learned prior 'improves training efficiency and generalization' for robotics (Abstract) overstates the evidence. The robotics results (Sec 4.2) are limited to a single simulated pick-and-place task (MolmoSpaces) and a trajectory-finetuning experiment on DROID. No closed-loop real-robot experiments were conducted (as admitted in Limitations), and the generalization claim is not supported by diverse real-world robotic benchmarks.
- **[science]** The claim that predicted trajectories provide 'effective motion guidance' for video generation resulting in 'more realistic object motion' (Abstract, Sec 4.3) relies on VBench metrics which measure consistency and smoothness, not physical realism. The paper does not provide a physical simulation-based evaluation or human study to substantiate the claim of 'more realistic' motion compared to larger baselines like Wan2.2.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper aggregates 1.16M videos from public sources (e.g., Xperience, YT-VIS) without explicit mention of consent for 3D motion annotation or downstream model training. Add a statement in Section 3.1 or the Appendix confirming that all source data complies with original licenses and that no personally identifiable information (PII) or sensitive biometric data was retained or used.
- **[writing]** The robotics transfer section (Sec 4.2) claims improved 'closed-loop success' in simulation but explicitly states 'We leave closed-loop real-robot evaluation to future work.' Given the potential for physical harm in real-world deployment, the paper must include a dedicated 'Safety and Limitations' subsection discussing the risks of deploying this model on physical hardware without further safety validation.
- **[writing]** The data pipeline uses LLMs (Molmo2, Qwen3) to generate captions and object phrases for 1.16M clips. There is no discussion of potential bias amplification or the inclusion of harmful/unsafe action descriptions in the training corpus. A brief statement on the filtering of unsafe content or the limitations of the automated curation regarding safety is required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The evaluation protocol relies on 'best-of-5' sampling for all baselines (Sec 4.1), but the text does not explicitly state if the proposed MolmoMotion models also used best-of-5 or a single deterministic pass. If MolmoMotion used a single pass while baselines used sampling, the reported ADE/FDE improvements are inflated. Clarify the sampling strategy for all methods in Tab 1.
- **[science]** The claim that pixel-space methods (Wan2.2, Cosmos) perform poorly on metric 3D tasks (Tab 1) relies on a post-hoc lifting pipeline (Sec 4.1 Baselines). The error introduced by this specific lifting pipeline (ViPE + AllTracker) is not quantified separately from the video generator's failure. A control experiment showing the lifting pipeline's error on ground-truth video frames is needed to isolate the generator's contribution to the metric error.
- **[science]** The robotics transfer results (Fig 3a) show a large gap in success rates (51% vs 19% at 10K steps). The text attributes this to the motion prior, but does not report the variance (standard deviation) across the 4 splits (SS, SU, US, All) or the number of seeds used for the policy training. Without variance estimates, the statistical significance of the 'substantial improvement' claim is unclear.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard deviations for all quantitative metrics in Table 1 (motion prediction) and Table 2 (video generation). The current presentation of single-point estimates (e.g., ADE=0.109) lacks statistical context regarding variance across the 742 benchmark clips, making it difficult to assess the robustness of the reported improvements over baselines.
- **[science]** Clarify the statistical methodology for the 'best-of-5' evaluation mentioned in Sec 4.1. Specify whether the final metric is the mean of the best-of-5 samples or the best-of-5 mean, and provide the variance across these selection events to ensure the reported gains are not artifacts of selection bias.
- **[science]** In the robotics transfer section (Sec 4.2), the success rates (e.g., 76.3% vs 56.0%) are presented without error bars or significance testing. Given the stochastic nature of robot policies and the finite number of evaluation episodes, a statistical test (e.g., bootstrap confidence intervals or a t-test) is required to substantiate the claim of 'substantial improvement'.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, correct the subject-verb agreement error: 'MolmoMotion is able to accurately predicts' should be 'accurately predict'.
- **[writing]** In Section 3 (Method), fix the typo 'varients' to 'variants' in the paragraph describing the second training stage.
- **[writing]** In Section 4 (Experiments), the phrase 'much larger image-to-video models' in the Introduction summary is vague; consider specifying the parameter counts or model names for clarity.
- **[writing]** In the Conclusion, the sentence 'This work would not be possible without...' contains a grammatical error: 'would not be possible' should be 'would not have been possible' to match the past tense context.
