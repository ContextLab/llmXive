# Automated-review action items — EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 1, the claim 'no system exceeds 0.5 on both EVA-A and EVA-X pass@1' is supported, but the text implies a stricter gap. Ensure the narrative aligns precisely with Table 1 data (GPT-Realtime: 0.467/0.566) to avoid overgeneralization.
- **[writing]** In Section 3.2, the phrase 'meeting the human IAA ceiling' is ambiguous. Clarify if this refers to a specific baseline human-human agreement study or simply 'human-level' agreement, as 'ceiling' implies a theoretical maximum not defined here.
- **[writing]** In Section 3.3, the claim 'S2S systems dominate EVA-X (mean turn-taking 0.82–0.83...)' conflates the Turn-Taking sub-metric with the aggregate EVA-X score. Explicitly state these are sub-metric scores, not the composite EVA-X pass@1 values.
- **[writing]** In Section 3.3, the claim '81% significant degradation' for turn-taking lacks a denominator. Specify if this refers to 81% of systems, scenarios, or trials to make the statistic verifiable.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Violates policy' subplot (bottom-right) has a y-axis label 'Cascade' but the data point (blue circle) is positioned at ~0.53, which contradicts the caption's claim that error bars are 95% bootstrap intervals over systems-within-type; the interval shown is extremely narrow and does not reflect the spread of the faint dots (individual systems) which range from ~0.3 to ~0.6. This suggests the error bar may be miscomputed or mislabeled.
- **[writing]** Figure 1: The x-axis label 'Rate (lower is better)' for the 'Violates policy' subplot is correct, but the y-axis labels ('Cascade', 'Hybrid', 'S2S') are not aligned with the data points — the blue circle for 'Cascade' is at ~0.53, yet the faint dots (individual systems) for Cascade span from ~0.3 to ~0.6, making the mean position ambiguous without a clear horizontal line or marker for the mean.
- **[science]** Figure 1: The 'Hybrid' row shows only faint diamond-shaped dots (n=2) with no aggregated mean or error bar, which matches the caption’s note that 'Hybrid (n=2) is shown as individual system points only.' However, the 'S2S' row shows a purple square with an error bar and a value of 0.83 (n=3), but the faint dots (individual systems) for S2S are clustered tightly around 0.8–0.9, suggesting the mean should be closer to 0.85–0.87, not 0.83 — possible miscalculation or mislabeling of the mean value.
- **[fatal]** Figure 2: The x-axis labels listing the specific models (e.g., 'Cascade: + + , ElevenAgents...') are completely missing from the rendered image, making it impossible to identify which bars correspond to which systems despite the caption's detailed list.
- **[science]** Figure 2: The caption states 'Hybrid ($n=2$) is shown as individual system points only' (referencing Figure 1's style), but the rendered figure shows bar charts for the Hybrid section, creating a contradiction between the visual representation and the description of the data presentation.
- **[writing]** Figure 2: The figure title 'Mean Delta' and the caption text 'Perturbation effect on across all evaluated systems' contain a missing metric name (e.g., 'conversation progression'), rendering the specific dependent variable undefined.
- **[fatal]** Figure 3: The x-axis lacks labels identifying the specific systems (e.g., 'ElevenAgents', 'Google', etc.) corresponding to the bar clusters; the caption lists them in text, but the plot itself is unreadable without them.
- **[fatal]** Figure 3: The legend mapping bar colors (teal, yellow, dark blue) to perturbation conditions (accent, background noise, both) is missing from the figure and not defined in the caption.
- **[fatal]** Figure 4: The x-axis labels listing the specific models (e.g., 'Cascade: + + , ElevenAgents...') are completely missing from the rendered image, making it impossible to identify which bars correspond to which systems despite the caption's detailed list.
- **[fatal]** Figure 4: The y-axis label 'Mean Delta' is present, but the caption text 'Perturbation effect on across all evaluated systems' contains a missing metric name (likely 'task completion' based on the filename), rendering the figure's specific subject ambiguous.
- **[science]** Figure 4: The caption states 'Hybrid ($n=2$) is shown as individual system points only' (referencing Figure 1's convention), yet the Hybrid section in this figure displays grouped bars with error bars, contradicting the stated visualization method for that architecture.
- **[fatal]** Figure 5: The x-axis is completely missing labels; the caption lists specific models (e.g., 'Cascade: + +', 'ElevenAgents') that are not mapped to the bar groups in the image.
- **[fatal]** Figure 5: The y-axis label 'Mean Delta' is present, but the caption text 'Perturbation effect on for cascade systems' contains a missing metric name (likely 'transcription accuracy'), making the figure's specific claim ambiguous.
- **[science]** Figure 5: The caption states 'Models, left to right: Cascade... Hybrid... S2S...', but the visual grouping of bars does not clearly demarcate these architecture categories, making it impossible to verify the model ordering.
- **[science]** Figure 6: The x-axis lacks labels identifying the specific models or systems represented by the bar clusters; the caption states 'Models listed in Appendix' but does not provide the mapping needed to interpret the data.
- **[science]** Figure 6: The y-axis is labeled 'Mean Delta' but lacks units or a metric name (e.g., 'Pass@1', 'Score'), making the magnitude of the perturbation effects ambiguous.
- **[writing]** Figure 6: The caption contains unrendered LaTeX formatting artifacts (e.g., 'pertaccent$$', 'pertbgnoise$$') that should be cleaned up for readability.
- **[science]** Figure 7: The caption states 'Models are sorted ascending,' but the bars are sorted descending (0.971 at top to 0.592 at bottom).
- **[science]** Figure 7: The caption contains unrendered placeholders ('aggregates the two cascades...', 'saturates near 1.0...', 'gap to the next-best STT ()') where model names should be, making the text unintelligible.
- **[writing]** Figure 7: The y-axis labels are truncated (e.g., 'Scribe-v2.2-Realtime' is cut off at the left edge), reducing readability.
- **[writing]** Figure 8: The caption lists 'EVA-A and EVA-X , , and scores' with missing metric names (likely Task Completion, Turn Taking, etc.), which are clearly defined in the figure's 'Voice Agent Quality Measurements' panel but not in the text.
- **[writing]** Figure 8: The 'Conditions' box lists 'K=5' and 'K=3' trials, but the caption does not define what 'clean' vs 'perturbed' runs correspond to these values, requiring the reader to infer from the 'Available Perturbations' box.
- **[science]** Figure 9: The caption claims 'four systems are on the Pareto frontier' (two S2S and two cascade), but the plot's dashed line connects only the two S2S points; the two high-performing Cascade points are not connected to the frontier line.
- **[writing]** Figure 9: The caption contains unreadable placeholders ('and ,', '+ + , and + +') where specific system names or metrics should be, making it impossible to identify the systems on the frontier.
- **[writing]** Figure 9: The caption text 'On the plot, only the two S2S systems are on the frontier' contradicts the earlier claim that four systems are on the frontier, creating confusion about the plot's content.
- **[writing]** Figure 10 caption is truncated mid-sentence at the end of the description for panel (b) ('shaded [threshold_sensitivity.pdf]'), cutting off the explanation of the shaded bands.
- **[writing]** Figure 10 caption contains unrendered LaTeX placeholders ('$_tt$', 'and thresholds') instead of formatted text or variable names.
- **[writing]** Figure 11: The caption describes the plot as a 'correlation' but the figure displays a scatter plot of individual system data points with an OLS fit line; the caption should explicitly state it shows the correlation between mean transcription accuracy and mean task completion.
- **[science]** Figure 11: The x-axis label 'Mean transcription accuracy on key entities' is ambiguous regarding the specific metric used (e.g., exact match vs. fuzzy match), which is critical for interpreting the high correlation values shown.
- **[writing]** Figure 12: The legend is illegible due to small font size and overlapping text, making it impossible to distinguish between the 12 evaluated systems listed.
- **[science]** Figure 12: The caption states the k=5 point is identically zero, but the plot shows lines converging to a non-zero value on the y-axis for k=5 in several panels (e.g., EVA-A pass@1, Task Completion), contradicting the description.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'LALM' at first use in Section 3.2. The term appears in the Introduction and Methodology without definition, relying on the Appendix for clarity. Replace with 'Large Audio-Language Model' or define inline.
- **[writing]** Replace the acronym 'S2S' with 'Speech-to-Speech' on first occurrence in the Introduction and Section 3.1. While defined in the Appendix, it is used frequently in the main text before the reader reaches the definitions.
- **[writing]** Define 'pass@k' and 'pass^k' (reliability metric) at their first introduction in Section 3.2. The mathematical notation is provided, but the plain-English distinction between 'ceiling performance' and 'reliability' should be explicit before the formula.
- **[writing]** Replace 'IAA' with 'inter-annotator agreement' in Section 4.2. The acronym is used without prior definition in the main text, assuming reader familiarity with this specific metric abbreviation.
- **[writing]** Define 'VAD' (Voice Activity Detection) at first use in Section 4.1 or the Limitations. The term is used to explain timing inaccuracies but is not defined in the main body or the Appendix definitions list.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Metric Definition vs. Qualitative Label: The definition of pass@k in the Appendix (fraction of scenarios with $\ge 1$ passing trial) is mathematically sound. However, labeling this as "ceiling performance" in Section 3.2 is logically imprecise. "Ceiling" typically denotes the maximum achievable performance limit, whereas pass@k is a probabilistic measure of success rate across trials. If a system has a 0.9 probability of passing a single trial, pass@k (for k=5) will be very high, but it does not
- **[writing]** Dominance Claim Nuance: The claim that S2S systems "dominate" EVA-X based on a mean turn-taking score of ~0.82 (just above the 0.8 threshold) versus ~0.4 for cascades is logically supported by the data. However, the text does not explicitly highlight that the S2S "dominance" is a marginal pass rather than a robust superiority in all aspects. Given that the turn-taking metric is binary-pass (threshold 0.8), the "dominance" is effectively a pass/fail distinction. The logic holds, but the interpret

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim 'no system exceeds 0.5 on both EVA-A and EVA-X' (Sec 1) is technically true but misleading given GPT-Realtime scores 0.47/0.57. Clarify if this implies a hard ceiling or simply that no system cleared the threshold, as the 0.47 score is very close.
- **[writing]** The conclusion 'S2S leads in experience, cascade in accuracy' (Sec 6) overstates the data. Table 1 shows a cascade system (Scribe+Gemini) scoring 0.49 EVA-A, higher than the best S2S (0.47). Qualify this as a general trend rather than a strict architectural rule.
- **[writing]** The phrase 'mean Δ up to 0.314' (Sec 1) is ambiguous. If 0.314 is a worst-case outlier, calling it a 'mean' is incorrect. Specify if this is an average across systems or a specific maximum drop to avoid misrepresenting robustness.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Ethics Statement (Sec. Ethics) explicitly admits the framework 'cannot guarantee models won't generate harmful output' and recommends content filtering. The paper must clarify if the evaluation protocol includes a mechanism to detect, log, or mitigate harmful outputs (e.g., PII leakage, hate speech) during the bot-to-bot simulation, or if this is a known limitation that requires a stronger disclaimer.
- **[writing]** The 'Limitations' section notes that 'No assessment of harmful outputs or PII exposure' was performed. Given the use of synthetic scenarios involving healthcare (HRSD) and airline data, the authors should explicitly state whether the synthetic data generation process included safeguards to prevent the inadvertent creation of realistic-looking PII (e.g., fake SSNs, medical IDs) that could be misused if the dataset is released.
- **[writing]** The evaluation relies on commercial APIs (OpenAI, Google, ElevenLabs) for both the agents and the judges. The paper should address the data privacy implications of sending conversation audio and transcripts to these third-party providers, specifically confirming whether data is used for model training or retained, as this impacts the 'no real caller data' claim.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Clarify the statistical basis for the 'median gap of 0.44' between pass@k and pass^k. The text implies this is a robust finding, but the variance decomposition (p < 0.0001) only addresses judge vs. trial variance, not the distribution of the gap itself across systems. Provide the standard deviation or confidence interval for this gap to support the claim of 'reliability divergence'.
- **[science]** The robustness analysis relies on a single accent (French) and a single noise environment (coffee shop) to claim 'asymmetric' architectural degradation. With n=1 per condition, these results may reflect specific voice properties rather than general accent/noise robustness. Explicitly frame these as preliminary findings or expand the perturbation suite to include at least one additional accent and noise type to support generalizable claims.
- **[science]** The 'Faithfulness' metric relies on LLM-as-Judge (Claude Opus 4.6) with a pass threshold of 0.5. While IAA is reported (kappa 0.777-0.845), the paper does not report the false-positive/false-negative rates of the judge against the human gold standard. Given that 72.2% of conversations show deviations, the sensitivity of the metric to actual policy violations versus stylistic preferences needs quantification to validate the 'decoupling' claim.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports p-values for variance decomposition (p < 0.0001) and correlation (p = 0.002) but does not specify the statistical tests used (e.g., F-test, t-test, permutation test) or the degrees of freedom. Explicitly state the test statistic and null hypothesis for all reported p-values to ensure reproducibility.
- **[science]** The perturbation analysis (Section 4.3) reports mean deltas and significance asterisks but lacks a description of the multiple-comparisons correction method (e.g., Bonferroni, Holm-Bonferroni, FDR) applied across the numerous architecture-perturbation-metric combinations. Without this, the reported significance levels may be inflated due to Type I error accumulation.
- **[science]** The confidence intervals for the main results (Table 1) are reported as standard errors (e.g., 0.207 ± 0.041). For binary pass/fail metrics aggregated over scenarios, standard errors may not accurately reflect the distribution of the estimator. Clarify if these are standard errors of the mean or 95% confidence intervals, and justify the choice of error metric given the non-normal distribution of pass rates.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Experiment Setup), the label command contains a space: `\label{sec: experiment-setup}`. This will cause a LaTeX compilation error or broken cross-references. Remove the space to match the standard `\label{sec:experiment-setup}`.
- **[writing]** In Section 3.2 (Evaluation Reliability), the text states 'Judge IAA ($\kappa$) ranges 0.777–0.845'. The en-dash usage is inconsistent with the rest of the document which often uses hyphens or specific ranges. Ensure consistent punctuation for numerical ranges throughout the manuscript.
- **[writing]** In the Introduction, the phrase 'median \passatk--\passpowerk~gap' uses a double hyphen for an en-dash. While common in LaTeX source, ensure the final compiled PDF renders this correctly as an en-dash. If not, replace `--` with `--` (LaTeX en-dash) or `\textendash` for clarity.
- **[writing]** In Section 4.1 (Main Findings), the sentence 'S2S systems dominate EVA-X (mean turn-taking 0.82–0.83 vs. cascade 0.28–0.58)' uses en-dashes for ranges. Verify consistency with other numerical ranges in the paper (e.g., Section 3.1 uses '0.777–0.845'). Standardize the character used for ranges (en-dash vs. hyphen) across the entire document.
