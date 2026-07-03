# Automated-review action items — Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Personality?

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The claim '51% of correct ratings are not grounded' equates MCQ failure with lack of grounding. Failing a specific probe does not prove absence of internal grounding; the text should clarify this is 'failure to retrieve the specific cue in the MCQ'.
- **[writing]** The EU AI Act citation implies a mandate for 'evidence trails' in the form of frame-accurate bounding boxes. The Act requires transparency, not this specific technical implementation. Rephrase to 'motivates the need for explainable evidence' rather than 'mandating'.
- **[writing]** The text states the Open-source Top-3 mean PR is ~47.0%. Based on Table 1 values (41.5, 47.0, 56.4), the mean is 48.3%. The value 47.0 appears to be a single model's score, not the mean. Correct the statistic or the model selection.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2(b): The 'Per-video density' table lists 'Trait analyses / video' as 5, but the sunburst chart (a) shows 'Task 1 Personality Rating' covers 1,104 videos. The table metric 'Trait analyses' is undefined and does not match the task count in the chart, creating a discrepancy in the reported data density.
- **[writing]** Figure 2(a): The outer ring labels for the 'Visual Grounding' and 'Reasoning' categories are rotated and tightly packed, making text like 'TSInt 849q' and 'Spat 1007q' difficult to read without zooming.
- **[fatal]** Figure 4: The figure has no caption (labeled '(no caption)'), making it impossible to verify what the radar chart represents or define the data series without guessing.
- **[science]** Figure 4: The chart title mentions 'Top-3 Closed' but the legend only defines 'Top-3 Proprietary' and 'Top-3 Open-source'; the mapping between 'Closed' and 'Proprietary' is assumed but not explicitly stated in the figure or caption.
- **[writing]** Figure 4: The axis labels (e.g., 'Personality Attribution', 'Counterfactual') are colored to match the data series, but the legend does not explain this color-coding scheme, creating potential confusion about whether the colors represent categories or data series.
- **[science]** Figure 5: The caption claims the tool displays a 'bbox overlay on the current frame,' but the video player shows a person in a car with no visible bounding boxes or geometry overlays.
- **[science]** Figure 5: The caption describes a 'Three-pane layout' with specific annotation controls, but the screenshot shows a 'MCQ Questions' tab with multiple-choice options, which contradicts the described 'atomic-cue list' and 'edit controls' for bounding boxes.
- **[writing]** Figure 6: The title and caption use the symbol '$$' to denote the drop metric, but the figure's x-axis labels and colorbar use the symbol 'Δ' (Delta). This inconsistency between the rendered text and the caption description is confusing.
- **[writing]** Figure 6: The colorbar label 'Judge score (1-10)' is ambiguous; it is unclear if this scale applies to the raw T2 scores in the first two columns or the drop values in the third column, as the drop values (e.g., 1.22) fall outside the typical 1-10 range implied by the label.
- **[writing]** Figure 7: The main title 'Neuroticism is the universally hardest Big Five trait' is redundant with the caption and should be removed to reduce clutter.
- **[science]** Figure 7: The y-axis label 'Mean T1 accuracy (%)' is technically correct but the caption frames the figure as 'difficulty'; adding a secondary label or note clarifying that lower accuracy equals higher difficulty would improve immediate interpretability.
- **[science]** Figure 8: The y-axis is labeled 'Score / Accuracy' but plots T2-Avg4 values scaled by 10 (e.g., 5.96 becomes ~60) alongside T1/T3 percentages (e.g., 51.3). This mixing of unscaled percentages and scaled raw scores on a single axis without explicit unit differentiation for each series is misleading and obscures the true magnitude of the T2 metric.
- **[writing]** Figure 8: The x-axis labels use inconsistent formatting for the parameter bands; the first group is labeled '≤8B' while the caption describes it as '8B', and the third group is '100B+' while the caption uses '100B+'. While minor, the visual label '≤8B' contradicts the caption's '8B' description.
- **[science]** Figure 9: The x-axis label 'T2-Avg4 (1-10)' indicates a 1-10 scale, but the y-axis is labeled 'Score / Accuracy' with a 0-70 range. This implies the T2 scores were scaled by 10 to match the axis, but this transformation is not explicitly stated in the caption or axis labels, making the direct visual comparison of bar heights misleading.
- **[writing]** Figure 9: The delta values ($\Delta$) are color-coded (black vs. red) to indicate magnitude, but there is no legend or text in the caption explaining the threshold for this color change.
- **[science]** Figure 10: The 'Trustworthy zone' is defined in the plot as T1 ≥ 50% and PR ≤ 30%, but the caption 'Right Rating, Wrong Cues' and the title 'Only 5 of 27 MLLMs reach the Trustworthy zone' do not explain the specific criteria for 'Trustworthy' or the significance of the 50%/30% thresholds, leaving the reader to guess the benchmark's success criteria.
- **[writing]** Figure 10: The y-axis label 'Prejudice Rate, PR (%) ↓ better correct ratings without retrieved cues' is grammatically confusing and cluttered; it should be split or rephrased to clearly indicate that lower PR is better and define what PR measures.
- **[writing]** Figure 10: The x-axis label 'Task 1 accuracy (I%) → better' contains a likely typo ('I%' instead of '%'), which reduces professionalism and clarity.
- **[science]** Figure 12: The legend defines 'Drops ≥5' and 'Climbs ≥5', but the plot contains many gray lines connecting points with rank differences clearly greater than 5 (e.g., Gemini 2.5 Flash moves from ~25 to ~4, a change of 21 ranks). This contradicts the caption's definition of 'Stable (|Δ|<5)'.
- **[writing]** Figure 12: The y-axis label 'Rank (1 = best)' is present, but the axis ticks are inverted (0 at top, 25 at bottom) without explicit indication, which can be confusing for readers expecting standard Cartesian coordinates.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on custom LaTeX macros and unexplained acronyms that hinder accessibility for non-specialist readers. In the Introduction, the term \\gapinv is used to denote the "Prejudice Gap," but the macro itself is opaque; the text should explicitly state "Prejudice Gap (PRG)" or similar on first mention rather than relying on a command. Similarly, in Section 4.2, the metric "RGM" (Rating-Grounding Misalignment) is introduced via Equation 4 without a textual definition of the

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a novel benchmark (MM-OCEAN) and a compelling high-level narrative distinguishing "perception" from "prejudice." However, several core logical links between the proposed metrics and the final conclusions are tenuous or confounded. First, the central claim of a "Prejudice Gap" (51% of correct ratings lack evidence) rests on the definition of the Prejudice Rate (PR). The paper defines PR as the probability that a model fails the grounding MCQ (T3) given it passed the rating task

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The '51% ungrounded' claim (Abstract) relies on fixed thresholds. Provide a sensitivity range for this metric or clarify it is threshold-dependent to avoid over-claiming a fixed statistic.
- **[science]** The 'significant' -26.6% gap between Top-3 closed/open models (Sec 5.1) lacks a statistical significance test (e.g., t-test) for n=3 groups. Replace 'significant' with 'large observed' or add statistical validation.
- **[writing]** The 'pervasive' Prejudice Gap claim (Conclusion) overgeneralizes from Western-centric, short-video data. Qualify the scope to the dataset's specific constraints in the main conclusion.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript addresses a critical safety concern: the distinction between genuine perception and algorithmic prejudice in personality assessment. The "Prejudice Gap" metric is a valuable contribution to safety evaluation. However, several ethical and safety gaps require attention before publication. First, the Ethics and Responsible Use section (Appendix E) is currently too brief regarding the specific risks of the new annotations. While the authors acknowledge the Western bias inherited from

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The 'Reasoning Capability' analysis (Appendix E002, Tab:reasoning) is observational and explicitly confounded by model size and family. The claim that reasoning capabilities drive the HR/PR gap requires a controlled ablation (e.g., same base model with/without RL) or a regression analysis controlling for parameters to rule out size as the primary driver.
- **[science]** The 'Prejudice Gap' (PR) metric relies on the assumption that T3 MCQs perfectly capture the evidence used for T1 ratings. The paper notes 153 'human-only' questions (1.8%) and varying difficulty. A sensitivity analysis is needed to show that the 51% PR statistic is robust to the inclusion/exclusion of these ambiguous or extremely difficult items, rather than being an artifact of the specific MCQ distractors.
- **[science]** The AI-as-Judge for Task 2 (T2) shows a self-preference bias of +1.0 point for GPT-4o-mini (Tab:cross_judge). While the authors argue this doesn't distort ranking, the absolute score inflation could impact the calculation of the 'Holistic-grounding Rate' (HR) if the T2 threshold (theta_2=0.7) is sensitive to this bias. Report HR sensitivity to a +/- 1.0 score shift.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for all aggregate metrics (e.g., mean PR, HR, T3 accuracy) in Table 1 and Section 5.1. Point estimates alone do not convey the stability of the 'Prejudice Gap' claim across the 27 models.
- **[science]** Clarify the statistical test used to validate the 'Closed vs. Open' gap (Section 5.1). A simple difference of means (14.5% vs 47.0%) is insufficient; provide a p-value or effect size (e.g., Cohen's d) from a t-test or non-parametric equivalent to support the claim of a 'significant' gap.
- **[science]** In Section 5.2 and Appendix A.10, the correlation between positional bias and T3 accuracy is reported as r ≈ -0.68. Specify if this is Pearson or Spearman correlation and provide the associated p-value to confirm statistical significance.
- **[science]** The AI-as-Judge robustness analysis (Appendix A.9) reports Spearman correlations (ρ=0.94, 0.92) but lacks confidence intervals for these correlation coefficients. Given the small sample size (n=200 for the subset), CIs are necessary to assess the precision of the rank stability claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains duplicate content across the main body and appendices. Specifically, Table 1 (Leaderboard) and Table 2 (MCQ Taxonomy) appear in both Section 4 and the Appendix with slight formatting variations. Consolidate these into the main text or the appendix to improve flow and reduce redundancy.
- **[writing]** In Section 5.2 (Diagnostics), the text references 'Figure 3' and 'Figure 4' for radar and archetype plots, but the LaTeX source defines them as Figure 3 and Figure 4 in the main body. However, the Appendix contains duplicate figure definitions (e.g., Fig: judge_reliability) that may cause compilation conflicts or confusion. Ensure unique label definitions and consistent cross-referencing throughout.
- **[writing]** The 'Code and Data Availability' section (end of main text) is extremely brief ('Available in project repository') and lacks the specific URLs provided in the critical elements list (e.g., GitHub/HuggingFace links). Expand this section to include direct links for reproducibility.
