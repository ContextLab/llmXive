# Automated-review action items — In-Context World Modeling for Robotic Control

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 4.1 claims '500 × 15 × 4 total episodes' for the LIBERO benchmark. However, the text specifies 4 suites, 8 training + 6 OOD viewpoints (14 total), and 500 episodes per viewpoint. The calculation 500 × 14 × 4 = 28,000, not 30,000. The '15' figure is unsupported by the stated protocol (8+6=14). Correct the total count or clarify the viewpoint split.
- **[writing]** Section 4.2 states 'standard VLA performance drops sharply from 68% to 17%'. Table 1 (Seen) shows the MV baseline average is 74.5% (Spatial) to 30.8% (Long), and Table 2 (Unseen) shows 48.3% to 19.8%. Neither the 68% (seen) nor 17% (unseen) figures match the reported averages in the tables. Verify the specific task or suite these numbers refer to, or correct them to match the table averages.
- **[writing]** Section 5.1 claims 'false context performs worse than no context at all (18.9 vs. 22.0)'. Table 3 confirms these averages. However, the text claims this negative transfer is 'symmetric in magnitude to the gains from correct context (+13.6%)'. The gain from 'w/o ctx' (22.0) to 'ICWM' (25.0) is +3.0, not +13.6. The 13.6% figure appears to be the drop from ICWM to 'w/o act' (25.0 -> 21.6), not the gain over 'w/o ctx'. Correct the comparison or the percentage cited.
- **[writing]** Section 5.3 claims 'ICWM consistently outperforms MV across all offsets with a stable margin of +60%'. Table 2 (Unseen) shows MV at 19.8% and ICWM at 25.0% (avg), a margin of ~5.2 points (26% relative). The text likely refers to the specific 80mm spacer case (MV 5.6 vs ICWM 14.4, which is ~157% relative increase, not 60%). The 'stable margin of +60%' claim is not supported by the aggregate data or the specific 80mm case. Clarify the specific condition or correct the percentage.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The 'OOD Viewpoint Shifts' bar chart lacks a Y-axis label defining the metric (e.g., Success Rate), making the quantitative claims ambiguous.
- **[writing]** Figure 1: The 'Real World Experiments' panel contains a text label '6 OOD Viewpoint' that is not defined in the caption or legend.
- **[science]** Figure 3: The caption claims the tasks are 'evaluated across six distinct camera viewpoints,' but the figure only displays a 'Multi-Cam View' and a 'Single Camera View' without showing or labeling the six specific viewpoints mentioned.
- **[writing]** Figure 3: The bottom section of the figure is partially obscured by large white blocks, cutting off the 'Single Camera View' label and the associated image sequence, making the figure incomplete.
- **[science]** Figure 4: The 'LONG' subplot shows 'UNSEEN' performance for MV, EXP, and ICWM that is higher than their 'SEEN' performance, which contradicts the definition of 'Unseen (OOD)' as a harder domain; verify if the x-axis labels are swapped or if the data is mislabeled.
- **[writing]** Figure 4: The 'LONG' subplot's 'UNSEEN' group lacks the small baseline bars (pi-FAST, pi-0.5, NORA) visible in other subplots, making it unclear if they are zero or missing data.
- **[writing]** Figure 5: The caption references items (a) and (b), but the figure uses numeric labels '1' and '2' instead; update the caption to match the figure or vice versa.
- **[writing]** Figure 5: The text 'Base:' appears in the lower-left white space without any corresponding image or explanation, creating confusion.
- **[fatal]** Figure 6: The figure has no caption provided ('(no caption)'), making it impossible to verify what the t-SNE plots represent or what the numerical labels (e.g., 45, 135) signify.
- **[science]** Figure 6: The x-axis scales differ between the 'Spatial' (-75 to 75) and 'Object' (-100 to 100) plots, which may mislead readers regarding the relative spread of the clusters without explicit normalization context.
- **[writing]** Figure 7: The caption 'Semantic perturbations' is too vague and does not describe the specific experiments, metrics, or conditions shown in the bar charts.
- **[science]** Figure 7: The bar charts lack axis labels and units, making it impossible to determine what metric is being measured (e.g., success rate, error) or the scale of the values.
- **[science]** Figure 7: The 'Morphology' section shows images of a robot with 'adding rigid spacers' but the corresponding chart labels refer to 'ΔL' (length change), creating a disconnect between the visual modification and the quantitative data.
- **[writing]** Figure 8: The caption contains a grammatical error ('different setting' should be 'different settings') and lacks specific details about the experimental conditions (e.g., hardware, model size) shown in the chart.
- **[science]** Figure 8: The x-axis label 'Inference Time Cost Per-step' is ambiguous; it is unclear if the values represent wall-clock time or computational cost, and the unit 's' (seconds) is only shown inside the bars rather than on the axis.
- **[writing]** Figure 10: The caption lists percentages as '100%, 90%, 80%, 70%', but the image labels show 'Original Length', '70% Length', '90% Length', and '80% Length'. The order and inclusion of 'Original' (vs 100%) are inconsistent between the text and the visual labels.
- **[writing]** Figure 10: The caption contains a formatting artifact '\100\%' which should be corrected to '100%' for proper typesetting.
- **[science]** Figure 11: The caption claims to illustrate 'robustness against object disturbances,' but the visualized trajectories show clean, successful executions without any visible perturbations or disturbances to the objects.
- **[writing]** Figure 11: The image contains three distinct task sequences (lifting, pick-and-place, stacking) labeled 1, 2, and 3, but the caption does not explicitly map these numbers to the specific tasks shown.
- **[fatal]** Figure 12: The caption is a placeholder ('Enter Caption') and does not describe the content, making the figure's purpose and the meaning of the labels ($o^s$, $o^e$) impossible to interpret.
- **[science]** Figure 12: The image consists of a grid of robot interaction pairs labeled $o^s$ and $o^e$ without any explanatory text or context, failing to communicate the scientific claim or comparison being illustrated.

## paper_reviewer_jargon_police — verdict: accept

The paper demonstrates a high standard of accessibility for a competent reader from an adjacent field (e.g., a robotics or machine learning PhD). The authors consistently define acronyms and notation at their first occurrence, ensuring that the specialized vocabulary of In-Context World Modeling (ICWM) does not create barriers to comprehension.

Specifically, the term "Vision-Language-Action (VLA)" is expanded in the abstract and again in the Introduction. The core acronym "In-Context World Modeling (ICWM)" is defined immediately upon introduction in the abstract and the Introduction. The symbol $\psi$ representing "system configuration" is explicitly defined in the Introduction and rigorously formalized in Section 3 ("Preliminary and Motivation") before being used in equations. Similarly, the interaction context $\mathcal{T}$ and the inference function $\Psi(\mathcal{T})$ are clearly defined in Section 3.2 and 4.1 respectively, with their roles in the equations explained in the surrounding prose.

The paper avoids undefined in-group shorthand. While it references specific benchmarks (LIBERO) and models (Qwen2.5-VL, FAST), these are standard in the field or accompanied by brief contextual descriptions (e.g., "action tokenizer" for FAST). The mathematical notation, including the POMDP formulation and mutual information terms, is introduced with clear definitions of the variables ($s_k$, $\xi_k$, $o_k$, $a_k$) and the assumptions (A1, A2) required for the propositions.

There are no instances of overloaded symbols or "obviously" statements that skip necessary definitions for an adjacent-field expert. The flow from problem formulation to method and experiments is self-contained regarding terminology. No action items are required.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.2 claims a 13.0% OOD improvement over MV, but Table 2 shows 25.0% vs 19.8% (5.2% diff). Correct the text to match the table or specify the subset.
- **[writing]** Section 4.2 claims a 9.5% OOD improvement over EXP, but Table 2 shows 25.0% vs 20.2% (4.8% diff). Align the text with the reported aggregate data.
- **[writing]** Section 4.3 claims false context loss is symmetric to a +13.6% gain, but Table 1 shows the gain (ICWM vs w/o ctx) is only 3.0%. The 13.6% figure matches the 'w/o actions' drop. Correct the symmetry claim.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper presents a strong core contribution regarding viewpoint generalization, supported by extensive simulation and real-robot experiments. However, the rhetoric in the Abstract, Introduction, and Conclusion occasionally overextends the scope of the demonstrated results to include semantic and morphological generalization as if they were equally robust findings. Specifically, the Abstract and Introduction frame the method as solving generalization to "novel setups" and "robot morphologies" b

## paper_reviewer_safety_ethics — verdict: accept

This work presents a method for In-Context World Modeling (ICWM) to improve robot generalization via test-time self-exploration. The research involves standard robotic manipulation tasks (stacking, lifting, pick-and-place) in simulation (LIBERO) and on a physical UR5e platform.

From a safety and ethics perspective, the paper is low-risk. The "active probing" phase described in Section 4.2 and Appendix B involves the robot executing random, task-agnostic movements within a pre-defined, kinematically constrained workspace to infer camera viewpoints and morphology. The authors explicitly state that this workspace is derived from the robot's joint limits and is designed to "avoid contact with task-relevant objects" and ensure motions remain within "operable joint limits." This is a standard safety procedure in robotics research (often called "calibration" or "self-probing") and does not constitute a dual-use capability for harm, surveillance, or deception.

There are no human-subjects data, PII, or sensitive datasets involved; the human demonstrations mentioned (Appendix B) are standard teleoperation logs for training, and the paper does not release raw video of humans or identifiable data. The method does not lower the barrier for cyber-attacks or biological hazards. No specific, non-trivial risks requiring mitigation or disclosure were identified in the text. The work adheres to standard norms for safe robotic experimentation.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling hypothesis: that self-generated interaction context can serve as a system identifier for VLA models. The experimental design is generally sound in its use of controlled baselines (MV, EXP) and ablation studies (w/o actions, w/o images). However, the evidentiary strength of the central quantitative claims is currently undermined by a lack of reported variance and potential confounds in the training setup. First, the headline result in Table 2 (25.0% vs 19.8% OOD su

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 1-3 report success rates to one decimal place but omit uncertainty metrics (SD/SE/CI). Given stochastic training, report mean ± SD across ≥3 seeds or state if single-seed results are used.
- **[writing]** Sections 4.2-4.3 claim 'significant' improvements without reporting p-values, CIs, or hypothesis tests. Either report test statistics/p-values for key comparisons or rephrase to 'higher average' without invoking significance.
- **[writing]** Tables 2-3 present multiple pairwise comparisons across viewpoints/ablations without multiplicity correction. If adding tests, apply Holm-Bonferroni or Benjamini-Hochberg correction to control false discovery rate.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the core argument flows logically from the problem statement to the proposed solution and validation. However, there are specific instances where sentence construction and paragraph organization impede the reader's momentum. In Section 4.2 (Real-world Results), the sentence beginning "As qualitatively shown in \autoref{fig:case}, while the base VLA exhibits..." is overly long and complex. It stacks a dependent clause, a contrastive clause, and a main cl
