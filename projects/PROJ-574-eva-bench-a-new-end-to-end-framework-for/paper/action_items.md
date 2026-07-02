# Automated-review action items — EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Replace the citation 'goodfeli/dlbook_notation' in the Introduction with a primary source on voice agent constraints (e.g., Stivers et al. 2009) as the current link is a LaTeX guide, not a scientific source for the claim.
- **[writing]** In the Introduction, clarify the rounding of the EVA-X score for gptrealtime. The text states 0.57 while Table 1 shows 0.566. Use the precise value or explicitly state the rounding convention to ensure factual precision.
- **[writing]** In 'Main Findings', clarify that the '0.28–0.58' range for cascade turn-taking refers to the observed range of individual system scores in Table 1, not a calculated mean, to ensure the claim is directly verifiable from the provided data.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Violates policy' subplot (bottom-right) has an x-axis labeled 'Rate (lower is better)' but displays values near 0.5–0.8, which are high violation rates — yet the caption and plot imply these are good outcomes. This contradicts the metric definition and misleads interpretation; either the axis label or the plotted values are incorrect.
- **[writing]** Figure 1: The legend at the bottom uses colored symbols (circle, diamond, square, dot) but does not explicitly map them to pipeline types in the legend itself — it relies on the caption’s text description ('Cascade', 'Hybrid', etc.), which is not visually linked to the symbols in the plot area. Add direct symbol-to-type labels in the legend for clarity.
- **[fatal]** Figure 2: The x-axis labels listing the specific models (e.g., 'Cascade: + + , ElevenAgents...') are completely missing from the rendered image, making it impossible to identify which bars correspond to which systems despite the caption's detailed list.
- **[science]** Figure 2: The caption states 'Hybrid ($n=2$) is shown as individual system points only' (referencing Figure 1's style), but the Hybrid section in this figure displays grouped bars with error bars, contradicting the description of how Hybrid data is presented.
- **[writing]** Figure 2: The y-axis label 'Mean Delta' is present, but the caption text 'Perturbation effect on across all evaluated systems' contains a missing metric name (likely 'conversation progression' based on the filename), rendering the figure's specific target undefined.
- **[fatal]** Figure 3: The x-axis labels listing the specific models (e.g., 'Cascade: + + , ElevenAgents...') are completely missing from the rendered image, making it impossible to identify which bars correspond to which systems as described in the caption.
- **[science]** Figure 3: The caption states that bar colors encode perturbation conditions (accent, background noise, both), but there is no legend in the figure or caption defining which color corresponds to which condition.
- **[fatal]** Figure 4: The x-axis is completely missing labels; the caption lists specific models (e.g., 'Cascade: + + , ElevenAgents...') but the rendered figure has no text under the bars to identify which system corresponds to which data group.
- **[fatal]** Figure 4: The y-axis label 'Mean Delta' is present, but the caption text 'Perturbation effect on across all evaluated systems' contains a missing metric name (likely 'task completion' based on the filename), making the figure's specific subject ambiguous.
- **[science]** Figure 4: The caption states 'Bar colors encode the perturbation condition' (accent, bgnoise, both), but the legend defining which color maps to which condition is missing from the figure itself.
- **[fatal]** Figure 5: The x-axis is completely illegible; model names and categories are missing, making it impossible to identify which systems correspond to the bar groups.
- **[fatal]** Figure 5: The y-axis label 'Mean Delta' is present, but the caption text 'Perturbation effect on for cascade systems' is missing the specific metric name (e.g., 'transcription accuracy'), rendering the figure's subject ambiguous.
- **[science]** Figure 5: The caption lists 'Hybrid' and 'S2S' models, but the figure title claims to show 'cascade systems' only; the x-axis labels (if visible) would be needed to verify if non-cascade models are incorrectly included.
- **[science]** Figure 6: The x-axis lacks labels identifying the specific models or systems represented by the bar clusters; the caption states 'Models listed in Appendix' but does not provide the mapping needed to interpret the data.
- **[science]** Figure 6: The y-axis is labeled 'Mean Delta' but lacks a unit or metric name (e.g., 'Pass@1', 'Accuracy'), making the magnitude of the perturbation effects ambiguous.
- **[writing]** Figure 6: The caption contains a typo 'Perturbation effect on pooled across domains' where the specific metric name is missing (likely 'EVA-X' based on the filename).
- **[science]** Figure 7: The caption states 'Models are sorted ascending,' but the bars are sorted descending (0.971 at top to 0.592 at bottom).
- **[science]** Figure 7: The caption contains unrendered placeholders ('aggregates the two cascades...', 'saturates near 1.0...', 'gap to the next-best STT ()') where specific model names should be, making the text unintelligible.
- **[writing]** Figure 7: The y-axis labels are truncated (e.g., 'Scribe-v2.2-Realtime' is cut off at the top), reducing readability.
- **[fatal]** Figure 9: The caption contains unrendered LaTeX placeholders ('and', 'mean $$ 95% CIs') and lists specific system names (e.g., '+ +') that are missing from the text, making the description of the plotted data unreadable.
- **[science]** Figure 9: The legend defines 'Hybrid (AudioLLM + TTS)' with a green diamond, but the caption states 'Hybrid (n=2) is shown as individual system points only' (referencing Figure 1's convention), creating a contradiction between the legend's implication of a mean point and the caption's description of individual points.
- **[writing]** Figure 9: The caption references 'On the plot' and 'On the plot' without specifying which subplots (e.g., (a) vs (b)) correspond to these descriptions, despite the text implying a comparison of axis ranges.
- **[writing]** Figure 10 caption is truncated mid-sentence at the end of the description for panel (b) ('shaded [threshold_sensitivity.pdf]'), cutting off the explanation of the shaded bands.
- **[writing]** Figure 10 caption contains unrendered LaTeX placeholders ('$_tt$') instead of formatted symbols (e.g., $t_{tt}$ or $	au_{tt}$), reducing readability.
- **[science]** Figure 11: The caption claims to show 'correlation' (a single aggregate statistic), but the plot displays 7 individual data points representing per-system means. The figure should be described as a scatter plot of 'Mean transcription accuracy vs Mean task completion' rather than a 'correlation' plot, or the caption should clarify that the correlation coefficient (r=0.930) is the result of the analysis shown.
- **[writing]** Figure 11: The title text 'Cascade systems: transcription vs task completion' and the statistical summary 'Pearson r = 0.930, p = 0.002, n = 7 systems' are rendered as part of the image title rather than being integrated into the caption or axis labels, which is inconsistent with standard scientific figure formatting.
- **[writing]** Figure 12: The legend is illegible due to small font size and dense text, making it impossible to distinguish between the 12 system names listed.
- **[science]** Figure 12: The caption states the k=5 point is 'identically zero' due to a single-anchor draw, yet the plot shows non-zero error bars (vertical lines) at k=5 for several metrics, contradicting the explanation.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'S2S' (Speech-to-Speech) and 'LALM' (Large Audio Language Model) at their first occurrence in the Introduction or Related Work, rather than deferring definitions to the Appendix.
- **[writing]** Replace the acronym 'IAA' (Inter-Annotator Agreement) with the full term or define it immediately upon first use in Section 4.2.
- **[writing]** Define 'VAD' (Voice Activity Detection) and 'STT' (Speech-to-Text) at first use in the Introduction or Methodology, as these are not universally known to non-specialist readers.
- **[writing]** Replace the term 'barge-in' in Section 3.2 with a plain English description (e.g., 'interrupting the agent') to improve accessibility for general readers.
- **[writing]** Define 'pass@k' and 'pass^k' (reliability metric) explicitly in the Introduction or Methodology before using them in the results, as they are central to the paper's claims.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logical framework for evaluating voice agents, but several conclusions do not strictly follow from the presented data or contain internal inconsistencies regarding metric definitions. First, the Introduction claims "no system exceeds 0.5 on both EVA-A and EVA-X pass@1." However, Table 1 (Section 4.3) lists the GPT-Realtime system with EVA-A pass@1 = 0.467 and EVA-X pass@1 = 0.566. While 0.467 is below 0.5, the phrasing suggests a hard frontier where *no* system comes close,

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The Abstract claim 'no system exceeds 0.5 on both EVA-A and EVA-X' is technically true but misleadingly absolute. It implies a hard frontier, whereas GPT-Realtime (0.467/0.566) is near-balanced. Rephrase to 'no system achieves simultaneous high performance (>0.5) on both metrics' to avoid implying a fundamental impossibility.
- **[writing]** The Conclusion states 'S2S systems lead in experience... while cascade systems lead in accuracy.' This overgeneralizes Table 1, where specific cascades (e.g., Scribe+GeminiFlash) outperform some S2S/Hybrid systems in accuracy, and some cascades outperform S2S in experience. Qualify the claim to reflect trends rather than strict architectural dichotomies.
- **[writing]** The Abstract cites a 'mean Δ up to 0.314' for robustness gaps. This value likely represents a worst-case drop, not a mean. Using 'mean' misleads readers about the average impact. Clarify as 'worst-case drop' or specify the exact metric and condition to ensure accurate interpretation of the robustness gaps.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The Ethics Statement (Section 6) explicitly admits the framework 'cannot guarantee models won't generate harmful output' and recommends content filtering. However, the paper lacks a dedicated 'Safety Evaluation' section or results quantifying the rate of harmful, biased, or PII-leaking outputs observed during the 12,780 trials. Given the high-stakes domains (Healthcare, Airline), this omission is a significant gap in the safety assessment.
- **[writing]** The 'Limitations' section notes that scenarios are in English and use only one French accent. This creates a potential fairness/bias risk where the framework may fail to detect safety failures (e.g., hallucinated medical advice) in underrepresented accents or languages. The authors should explicitly discuss this limitation as a safety concern, not just a performance one.
- **[writing]** The 'Reproducibility Statement' notes that full reproduction requires commercial API access. While acceptable for science, this creates a barrier for independent safety auditing of the framework's ability to detect harmful outputs. The authors should clarify if the synthetic data generation pipeline (SyGra) is fully open-sourced to allow third-party safety stress-testing without API costs.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Clarify the statistical basis for the 'median gap of 0.44' claim (Sec 1, Sec 4.3). The text states this is a median gap between pass@k and pass^k, but the calculation method (per-scenario vs. per-system) and the distribution of these gaps are not described. Provide the interquartile range or a histogram to demonstrate robustness against outliers.
- **[science]** Address the confounding variable in the robustness analysis (Sec 4.3, Limitations). The study uses only one specific French voice and one coffee shop noise profile. The claim that 'accent hits cascade accuracy' may reflect specific acoustic properties of that voice/noise pair rather than general accent robustness. Explicitly state this limitation as a threat to external validity or add a sensitivity analysis if data permits.
- **[science]** Justify the 'pass^k' reliability metric (Sec 2.2, App Defs). The metric assumes independent trials to calculate the probability of passing all k attempts. However, the text notes 'Trial stochasticity is the dominant variance source' (Sec 4.2). If trials share the same underlying model state or prompt seed, independence is violated. Confirm the randomization strategy (e.g., temperature, seed) used to ensure trial independence.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports p-values (e.g., p < 0.0001 for variance decomposition) but does not specify the statistical test used (e.g., Levene's, F-test) or the distributional assumptions. Given the non-normal nature of pass/fail metrics, clarify the test statistic and validity of the p-values.
- **[science]** Multiple comparisons are performed across 12 systems and 6+ metrics without correction (e.g., Bonferroni, Holm). With ~72+ pairwise tests implied, the risk of Type I error is high. Report adjusted p-values or justify the lack of correction.
- **[science]** Confidence intervals are reported as '±' standard deviations (e.g., 0.207 ± 0.041) in Table 1, but the text and figure captions refer to '95% percentile bootstrap intervals'. Standard deviation is not a confidence interval. Explicitly label these as SD or recompute as 95% CIs for consistency.
- **[science]** The correlation claim (Pearson r = 0.93, p = 0.002) between transcription accuracy and task completion is based on n=7 systems (cascade only). This sample size is insufficient for robust correlation inference. Report the exact test used and consider non-parametric alternatives (Spearman) given the small N.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Conversation Simulation), the phrase 'Automated checks for \metricbehavior~and \metricuserspeechfidelity' uses undefined LaTeX macros. Replace these with the full metric names (e.g., 'User Behavioral Fidelity' and 'User Speech Fidelity') or ensure the definitions are visible in the main text flow to avoid reader confusion.
- **[writing]** In Section 4.2 (Main Findings), the sentence 'S2S systems dominate EVA-X (mean turn-taking 0.82–0.83 vs. cascade 0.28–0.58)' lacks a clear subject for the comparison. Clarify whether these ranges refer to the mean scores across all S2S systems versus all cascade systems, or specific subsets, to ensure the statistical claim is unambiguous.
- **[writing]** In the Limitations section, the phrase 'LLM/LALM judges may exhibit stylistic biases (e.g., GPT-5.4 evaluated with GPT-5.2 judges)' is slightly confusing. Clarify if this refers to a version mismatch between the model being evaluated and the judge model, or a specific experimental setup, to prevent misinterpretation of the bias source.
