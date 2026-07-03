# Automated-review action items — ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time?

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify if the 87.1% human plausibility in Section 5.2 refers to the 2-of-3 axis acceptance rule in Section 3.1 or a separate probe validation step to avoid ambiguity.
- **[writing]** The claim that PTF sensitivity ranges from -8.8 to -23.0 overgeneralizes; Table 5 shows DeepSeek-V4-Pro has only -1.3 sensitivity to shuffling, contradicting the implied universal range.
- **[writing]** Explicitly cite the 'Dir' sub-metric in Table 5 to support the specific claim that DPO improves 'trajectory direction' rather than just overall fidelity.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and missing reference ('An example from :') where the dataset or section name should be.
- **[writing]** Figure 1: The timeline labels 'Book 1, Chap 10' and 'Book 5, Chap 130' are factually inconsistent with the Harry Potter series (Book 5 has only 38 chapters).
- **[writing]** Figure 3: The caption contains incomplete text ('Tables and .') and does not define the 'Per-category' groupings (e.g., HER-32B, CoS-ER-8B) shown on the x-axis.
- **[science]** Figure 3: The y-axis label 'Arc lift over best non-Arc (pts)' is ambiguous; it is unclear if 'pts' refers to percentage points, raw score points, or a normalized metric, as no unit definition is provided in the caption.
- **[science]** Figure 4: The caption describes an 'Arc source-of-effect ablation' but the Y-axis is labeled 'AvgPP' (Average Perplexity) without defining the metric or explaining how it relates to the ablation effect.
- **[science]** Figure 4: The X-axis labels 'DS-V4-Flash', 'Qwen3-32B', and 'ArcANE-32B-DPO' do not match the caption's claim of 'three models' if 'DS' is DeepSeek and 'ArcANE' is the proposed method; the specific ablation conditions (e.g., 'Vanilla' vs 'MixedArc') are shown in the legend but the grouping logic on the X-axis is unclear.
- **[writing]** Figure 4: The legend uses 'Vanilla', 'MixedArc', 'ArcHint', and 'Arc', but the caption does not define these terms or explain what 'Arc source-of-effect ablation' entails for each category.
- **[science]** Figure 6: The figure is a sunburst chart showing a taxonomy of character arcs, but the caption claims it shows 'Induced axes are clustered and grounded against established literary or psychological scholarship.' The visual does not display any clustering analysis, statistical grounding, or comparison to external scholarship, making the figure unsupported by the caption's claim.
- **[writing]** Figure 6: The caption cites 'Values in the Wild huang2025values' but the figure itself contains no visual elements (such as citations, references, or source labels) to demonstrate this grounding.
- **[science]** Figure 7: The caption states 'Arc-over-Vanilla Overall lift', but the y-axis is labeled 'Arc lift over Vanilla (pts)'. While similar, the term 'Overall' in the caption implies an aggregate or mean, yet the bars represent specific models (DS-V4-Flash, Qwen3-8B, etc.) rather than a single 'Overall' metric. The figure shows per-model lift, not an overall lift, creating a mismatch between the caption's claim and the data granularity.
- **[writing]** Figure 7: The x-axis labels are rotated at a steep angle and are partially cut off or difficult to read (e.g., 'DS-V4-Flash', 'Qwen3-32B'), reducing legibility.
- **[writing]** Figure 8: The caption identifies the image as an 'Annotation Page for LLm judges', but the screenshot displays a human annotation interface (radio buttons for 'Reasonable'/'Not reasonable', text input for comments) rather than an LLM judge's output or interface.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and specialized terminology that are not consistently defined for a general audience. In the Introduction, the term "RPLAs" (Role-Playing Language Agents) is used immediately without expansion, creating an immediate barrier for readers unfamiliar with the specific sub-field of agent evaluation. Similarly, in Section 3.1, the distinction between "intrapersonal" and "relational" axes is made without plain-language context, assuming the read

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling framework for evaluating temporal character consistency, but several logical gaps exist between the presented data and the broad conclusions drawn. First, the central claim in the Abstract and Section 4.3 that "conditioning on the Character Arc outperforms all other context strategies" is an overgeneralization not fully supported by Table 1 (e000). For the Qwen3-32B model in the "In-Scenario" category, the RAG mode achieves a higher Action Phase-Fidelity (APF) sco

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the 'Arc' context mode outperforms all others 'especially on Out-of-World scenarios where retrieval fails' (Sec 4.3) overstates the evidence. The paper does not explicitly demonstrate that RAG fails on these specific probes; it only shows Arc is better. The authors must clarify if RAG failure is a measured phenomenon or an assumption, and avoid implying causality without direct evidence of retrieval breakdown.
- **[writing]** The conclusion that DPO training 'specifically improves In-World and Out-of-World performance' (Sec 4.4) is an over-interpretation of the aggregate lift. The data shows a general lift across all categories. The authors should avoid attributing the gain specifically to 'trajectory direction' in out-of-text scenarios without a targeted ablation showing that SFT models fail specifically on trajectory direction in those specific scenarios, rather than just general fidelity.
- **[writing]** The assertion that 'retrieval fails' on Out-of-World probes (Sec 4.3) is a strong claim that requires validation. The paper defines Out-of-World as 'non-source era' but does not provide data showing that RAG systems actually retrieve irrelevant or zero-shot results for these specific prompts. The authors should either provide evidence of retrieval failure or rephrase the claim to 'where retrieval is less likely to be directly applicable' to avoid overreach.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Limitations section (Sec. 6) acknowledges that 'period-bound social attitudes' in 19th/early-20th-century texts may be reproduced. However, the paper lacks a concrete mitigation strategy for when RPLAs generate hate speech, slurs, or harmful stereotypes inherent to the source material (e.g., in 'Anna Karenina' or 'The Underdogs'). Explicitly state how the evaluation protocol handles or filters such outputs to prevent the benchmark from inadvertently promoting harmful content.
- **[writing]** The dataset construction relies on LLMs to generate 'psychologically impactful events' and 'character arcs' (Sec. 3.1). There is no mention of human oversight regarding the potential for these LLMs to hallucinate or introduce biased interpretations of sensitive psychological traits or traumatic events. Clarify the human-in-the-loop validation process for these specific psychological constructs to ensure they do not reinforce harmful stereotypes.
- **[writing]** The 'Out-of-World' probes (Sec. 3.2) transpose characters into non-source eras. While creative, this risks generating scenarios where characters are placed in contexts that could be interpreted as trivializing historical tragedies or misrepresenting marginalized groups. The paper should confirm that these probes were screened for potential ethical violations or offensive content before evaluation.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The PTF metric validity relies on a correlation of r=0.51 with per-phase averages (Appendix PTF Metric Validity). This indicates PTF captures only ~26% of the variance explained by simple averaging. The authors must provide a stronger statistical justification (e.g., variance decomposition or regression analysis) for why PTF is a distinct and necessary metric beyond a weighted average of APF/RPF/RAE.
- **[science]** The claim that DPO training specifically improves trajectory direction (Section 5.3) is based on a comparison of 1,198/1,750 probes. The evidence lacks a formal statistical test (e.g., paired t-test or Wilcoxon signed-rank) on the magnitude of the PTF improvement to rule out random variation, especially given the small sample size of the perturbation analysis (N=75 in Table 6).
- **[science]** The 'MixedArc' ablation (Section 5.1) uses a deterministic hash to select donor characters. The authors must clarify if this selection process introduces any systematic bias (e.g., selecting characters with similar arc structures) that could artificially inflate the 'Vanilla' baseline performance, thereby underestimating the true effect size of the correct Arc.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for all mean scores in Tables 1 and 2. The current presentation of single-point estimates (e.g., 62.4 vs 57.7) lacks a measure of uncertainty, making it impossible to assess the statistical significance of the reported gains without raw data.
- **[science]** Clarify the statistical test used to validate the 'PTF sensitivity' claims in Section 5.2 and Appendix B. The text reports specific point drops (e.g., -23.0) for perturbed conditions but does not state if these differences were tested against a null hypothesis or if the variance across the 75 probes was sufficient to support the conclusion.
- **[science]** Address the multiple comparisons problem. The study evaluates 6 models across 6 context modes and 4 metrics (APF, RPF, RAE, PTF) across 3 scenario types. The paper highlights 'best' results without mentioning any correction (e.g., Bonferroni, Holm-Bonferroni) for the large number of pairwise comparisons performed.
- **[science]** Provide the sample size (N) and degrees of freedom for the Pearson correlation analyses in Appendix B (Judge Validation). While r=0.96 is reported, the statistical power and significance (p-value) of these correlations are missing, which is critical for validating the LLM judge.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Character Arc Construction), the phrase 'inducing intrapersonal... axes grounded in scholarship' is slightly ambiguous. Clarify whether the axes are induced by the LLM or the human annotators, and ensure the citation placement clearly links to the theoretical grounding.
- **[writing]** In Section 4.2 (Evaluation Protocol), the definition of PTF ('assesses alignment, direction, and shape') is abstract. Consider adding a brief parenthetical example or a reference to the specific mathematical formulation in the Appendix to improve immediate clarity for the reader.
- **[writing]** In Section 5.1 (Source-of-effect ablation), the sentence 'ArcHint... recovers most of the gain for prompting but only half for trained models' lacks a clear subject for 'recovers'. Rephrase to 'The ArcHint condition recovers...' to ensure grammatical precision.
- **[writing]** Throughout the text, ensure consistent capitalization of 'Out-of-World' vs 'out-of-world'. The manuscript currently uses both forms (e.g., Abstract vs. Section 4.3). Standardize to one style for professional polish.
