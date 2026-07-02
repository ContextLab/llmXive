# Automated-review action items — SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio-cognitive Variations

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.2 claims '40 hard scenarios (5 per domain)' across 8 domains. While mathematically consistent, the specific 8-domain taxonomy lacks an external citation, appearing to be derived solely from the authors' agentic process. Clarify the source of this taxonomy.
- **[writing]** Section 4.1 states the evaluator 'more than doubles' ProMediate's performance (0.82 vs 0.37). Verify that the 0.372 baseline value is explicitly reported in the cited Liu et al. (2025) paper, not a new run by the authors, to ensure the comparison is valid.
- **[science]** Section 3.3 claims axes are applied 'independently' to 'isolate failure modes.' Without statistical interaction tests (e.g., ANOVA), this is a design intent, not a proven result. Soften the claim to 'designed to isolate' to avoid overstating the evidence.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and missing noun in the opening phrase ('Overview of : agentic scenario curation...'), likely omitting the system name 'SoCRATES'.
- **[writing]** Figure 1: The caption contains a grammatical error in the phrase 'expose where mediators fails', which should be 'fail' to agree with the plural subject.
- **[science]** Figure 2: The legend lists 8 models, but the caption states the figure measures 'Mediator adaptation' (singular). The radar charts show 8 separate subplots (a-h), one per model, rather than a single comparison of one mediator's adaptation across axes. This creates a disconnect between the caption's claim of 'adaptation' and the visual presentation of static performance profiles for multiple distinct mediators.
- **[writing]** Figure 2: The legend uses color to distinguish models, but the subplots (a-h) also use color to distinguish models. This redundancy is unnecessary and potentially confusing if the colors in the legend do not perfectly match the fill colors in the subplots (e.g., 'Gemini-3.1-FL' is red in the legend and red in (a), but 'Qwen3-30B' is blue in the legend and blue in (h)). The legend is redundant given the subplots are already labeled.
- **[writing]** Figure 2: The axis labels (GEN, SA, MS, LONG, EMO, CUL) are defined in the large left chart but are not explicitly defined in the caption. While the caption mentions 'five socio-cognitive axes', it does not map the abbreviations (e.g., 'SA' for Strategic Adaptation) to the full terms, forcing the reader to infer from the large chart.
- **[science]** Figure 3: The caption describes three axes (strategic posture, emotional reactivity, cultural identity), but the subplots are labeled with specific condition pairs (e.g., 'Avoiding', 'Accommodating', 'Com-Com', 'US-US') without defining which axis each column group represents, making the mapping between the caption's abstract axes and the concrete data ambiguous.
- **[writing]** Figure 3: The colorbars for the three subplots have inconsistent scales (e.g., -60 to 60 vs -40 to 40), which prevents direct visual comparison of the magnitude of consensus gain shifts across the different axes.
- **[science]** Figure 4: The caption claims to show results for 'five socio-cognitive axes' (General + 5 hard conditions), but the legend only lists 6 models (Average, Gemini 3-1 FL, GPT-5 6-m, DeepSeek V3.2, Gemma 4-25B, Nemotron 3-12B, Qwen 3-25B, Qwen 3-30B). There is no mapping between the models and the specific socio-cognitive axes (e.g., Strategic Posture, Emotional Reactivity) mentioned in the caption.
- **[writing]** Figure 4: The y-axis label 'Intervention Effectiveness' is present, but the unit or scale (e.g., percentage points, raw score) is not defined in the axis or caption, making the magnitude of the effect ambiguous.
- **[writing]** Figure 4: The x-axis label 'Conversation Progress (%)' is clear, but the caption's claim that 'turns are mapped to a 0--100% scale' is not visually represented; the plot shows discrete bins (0-20%, 20-40%, etc.) rather than a continuous scale, which may mislead readers about the data granularity.
- **[science]** Figure 5: The caption claims the figure shows three subplots (a, b, c) for strategic posture, emotional reactivity, and cultural identity, but the rendered image contains four distinct heatmaps with no subplot labels (a, b, c) to distinguish them.
- **[science]** Figure 5: The x-axis labels (e.g., 'Avoiding', 'Accommodating', 'Com-Com') do not match the categories described in the caption (strategic posture, emotional reactivity, cultural identity), making it impossible to verify which panel corresponds to which axis.
- **[writing]** Figure 5: The colorbars for the four heatmaps use inconsistent scales (e.g., -60 to 60 vs -40 to 40), which prevents direct visual comparison of the consensus gain shifts across the different conditions.
- **[science]** Figure 6: The caption claims to show 'Change in Consensus Gain' (a delta metric), but the y-axis is labeled 'Intervention Effectiveness' and the data trends (e.g., rising curves) contradict the expected behavior of a relative change metric which should center around zero or show degradation/improvement shifts.
- **[writing]** Figure 6: The caption text is identical to Figure 5's caption, yet the subplots (a, b, c) and data trends differ significantly; the caption fails to describe the specific axes or conditions shown in this figure.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that creates a barrier for readers outside the immediate subfield of LLM agent evaluation. While the concepts are sound, the density of jargon without immediate definition or plain-language equivalents reduces accessibility. First, the term "agentic" is overused as a standalone adjective (e.g., "agentic process," "agentic deep research," "agentic scenario curation"). In Section 1 and Section 3.2, this term is used to describe the methodolo

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Independence of Axes: The paper asserts that socio-cognitive axes are applied "independently" to isolate failure modes (Section 3.2). While the text states "no stacking," the "Cultural Identity" axis generates 6 conditions (US-US, CN-CN, KR-KR, US-CN, US-KR, CN-KR). This inherently involves varying the *composition* of parties (e.g., US vs. CN) which overlaps conceptually with the "Party Composition" axis (2 vs. 3 parties). If the "Party Composition" axis adds a third party, does the "Cultural I
- **[writing]** Metric Sensitivity: The "Consensus Gain" formula normalizes by $(1 - S^{unmed})$. Logically, if the unmediated baseline ($S^{unmed}$) is already high (e.g., 0.9), the denominator becomes very small (0.1). This makes the metric highly sensitive to minor absolute improvements in the mediated score, potentially exaggerating the "gain" in scenarios where the conflict was already nearly resolved without intervention. The paper does not address whether this normalization introduces a logical bias wher

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that the evaluator 'more than doubles' ProMediate's performance relies on comparing different backbones (DeepSeek vs. Qwen). Clarify if the gain holds when using the same backbone, or rephrase to avoid attributing the full gain to the method alone.
- **[writing]** The claim that 'scale alone does not order the field' is over-generalized from a single outlier (Nemotron vs. Gemma). Data shows strong scale correlation within families. Temper the claim to acknowledge scale is a strong predictor but not the sole determinant.
- **[science]** The claim that axes are applied 'independently' is contradicted by the Cultural Identity axis, which varies two parties' identities simultaneously (e.g., US-CN). This is a joint variation, confounding the attribution of performance drops to a single 'cultural' factor.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethical Considerations' section states scenarios are 'synthesized and anonymized' but the 'Agentic Scenario Curation' section explicitly describes using LLM agents to 'search the web for real public disputes' (e.g., the Mount Sinai hospital closure case in Table 5). The manuscript must clarify the exact boundary between real-world data ingestion and synthetic generation to ensure no PII or sensitive real-world details are inadvertently leaked in the benchmark scenarios.
- **[writing]** The validation of the 'Topic-localized Evaluator' relies on 1,844 dialogue snippets rated by 'two expert annotators' and 'MTurk workers' (Section 4, Appendix). The paper lacks a formal statement regarding IRB approval or exemption for this human-subject research. Given the nature of conflict simulation, a statement confirming ethical oversight and informed consent procedures for the annotators is required.
- **[writing]** The benchmark includes 'Cultural Identity' axes using Hofstede profiles for KR, US, and CN (Section 3.3). The paper must explicitly address the risk of reinforcing cultural stereotypes through these synthetic personas. A brief discussion on how the framework mitigates the potential for the evaluation to produce biased or harmful generalizations about specific cultures is necessary.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report confidence intervals or a significance test (e.g., Fisher's z) for the difference between the new evaluator's correlation (0.82) and ProMediate's (0.37) to statistically validate the 'doubling' claim in Section 3.2.
- **[science]** Provide variance estimates (standard error or CI) for the main benchmark results in Section 4. The current 'single-run' design (4,800 runs) makes it impossible to distinguish real mediator differences from stochastic noise without replication data.
- **[science]** Report effect sizes (e.g., Cohen's d) for the socio-cognitive axis impacts in Section 4.2. Raw percentage point drops (e.g., 18.9–64.1) are insufficient to claim 'sharp' variations without normalizing against baseline variance.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the primary benchmark metrics (Consensus Gain, Timeliness, Effectiveness) in Table 1 and Table 3. Currently, only point estimates are provided, making it impossible to assess the statistical significance of the reported differences between mediators (e.g., the 1.1–2.5 point gap between proprietary and open-source models).
- **[science]** Clarify the statistical test used to validate the 'doubling' claim for the evaluator's Pearson correlation (r=0.82 vs r=0.37). A simple comparison of correlation coefficients is insufficient; a Fisher's z-transformation or a permutation test is required to demonstrate that the improvement is statistically significant and not due to sampling variance.
- **[science]** Address the multiple comparisons problem in the socio-cognitive probing analysis. With 15 conditions and 8 mediators, numerous pairwise comparisons are made. The paper reports specific drops (e.g., '18.9–64.1') without indicating if these were corrected for family-wise error rate (e.g., Bonferroni) or false discovery rate (FDR).
- **[science]** The stability analysis reports Kendall's W = 0.929 for rankings across three runs. However, the raw variance (half-range) for Consensus Gain in Table 5 is substantial for some models (e.g., Nemotron-3-120B: ±6.8). Provide a formal test (e.g., ANOVA or mixed-effects model) to determine if the observed performance differences between mediators are robust against this run-to-run variance.

## paper_reviewer_writing_quality — verdict: accept

The manuscript demonstrates exceptional writing quality, characterized by clarity, logical flow, and precise academic prose. The authors effectively articulate the complexities of evaluating LLM-mediated conflict resolution, presenting the SoCRATES framework in a manner that is both accessible and rigorous.

The structure is well-organized, guiding the reader seamlessly from the introduction of the problem space through the methodology, validation, and experimental results. The introduction (Section 1) clearly establishes the motivation and contributions, while the Related Work section (Section 2) provides necessary context without becoming cluttered. The transition between the three core components of the framework—Agentic Scenario Curation, Socio-Cognitive Probing, and Topic-Localized Evaluation—is handled smoothly, with each subsection building logically on the previous one.

Sentence-level grammar is flawless, and the authors make excellent use of technical terminology without sacrificing readability. The definitions of key metrics (e.g., Consensus Gain, Intervention Timeliness) are precise and easy to follow. The use of active voice and concise phrasing enhances the overall impact of the text. For instance, the description of the "Topic-Localized Evaluation" mechanism in Section 3.3 is particularly clear, effectively explaining how the evaluator isolates relevant turns to reduce noise.

The paper also excels in its presentation of results. The text accompanying the tables and figures (e.g., Section 4.1 and 4.2) provides insightful analysis that complements the data, avoiding mere repetition of numbers. The authors successfully convey the nuances of their findings, such as the trade-off between intervention timeliness and effectiveness, with clarity and depth.

Minor stylistic choices, such as the use of bolding for key terms and the consistent formatting of mathematical expressions, contribute to the document's professional appearance. There are no instances of ambiguous phrasing, grammatical errors, or disjointed paragraphs that would impede understanding.

In conclusion, the writing quality of this paper is outstanding. It meets the highest standards of academic communication, making a complex technical contribution easy to understand and appreciate. No revisions are necessary regarding the writing.
