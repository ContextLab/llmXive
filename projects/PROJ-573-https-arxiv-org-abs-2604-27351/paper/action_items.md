# Automated-review action items — Heterogeneous Scientific Foundation Model Collaboration

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that EywaAgent improves utility by ~7% (Introduction) is inconsistent with Table 1 (0.6558 vs 0.6154, ~6.6%). While close, the text should match the reported table value or clarify the rounding method to ensure factual precision.
- **[writing]** The claim that Eywa reduces token usage by ~30% (Introduction) is supported by Table 1 (4469 vs 3137 tokens, ~29.8%). However, the text states 'nearly 30%' in Section 5.3 but 'reducing token usage by ~30%' in the Introduction. Ensure consistency in phrasing or precision across sections.
- **[writing]** The claim that EywaOrchestra 'surpasses' EywaMAS on several sub-domains (Section 5.3) is not fully supported by Table 1. EywaOrchestra has higher utility than EywaMAS in Space (0.7187 vs 0.6899), Clinic (0.5159 vs 0.5086), Drug (0.6319 vs 0.6248), and Business (0.7388 vs 0.7284). However, the text says 'surpasses it on several sub-domains' which is accurate, but the phrasing 'surpasses it' might imply a general trend. Clarify if this is limited to specific domains.
- **[writing]** The claim that 'heterogeneous LLM-only MAS methods do not consistently outperform strong homogeneous MAS baselines' (Section 5.3) is supported by Table 1 (MoA and X-MAS have lower utility than Refine and Debate in most domains). However, the text should explicitly reference the specific baselines (Refine, Debate) to avoid ambiguity about which 'strong homogeneous MAS baselines' are being compared.
- **[writing]** The claim that 'EywaAgent improves both quality and efficiency under the same backbone' (Section 5.3) is supported by Table 1 (0.6558 utility vs 0.6154, 3137 tokens vs 4469). However, the text should clarify that this comparison is against the 'Single-LLM-Agent' baseline (gpt-5-nano) to avoid confusion with other baselines.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The caption 'LLM Temperature Ablation' is too brief; it should explicitly state that the plot compares Overall Utility of EywaAgent, EywaMAS, and EywaOrchestra across the temperature range.
- **[science]** Figure 2: The y-axis 'Overall Utility' scale is truncated (0.63 to 0.69), which visually exaggerates the performance differences between the models; a full 0-1 scale or explicit note on truncation is needed to avoid misleading interpretation.
- **[science]** Figure 3: The caption claims distributions are 'near-uniform,' but the chart shows a 1.8x range (15 to 28) with no visual indication of statistical uniformity or error bars to support this claim.
- **[writing]** Figure 3: The y-axis label '# Samples' is ambiguous; it is unclear if these are raw counts or normalized percentages, which is critical for evaluating the 'uniformity' claim.
- **[writing]** Figure 5: The caption contains a formatting artifact ('$$') between 'nine sub-domains (inner ring)' and 'three modalities (outer ring)' which should be corrected to a standard separator.
- **[writing]** Figure 5: The caption claims 'All 27 cells are populated' (9 sub-domains × 3 modalities), but visual inspection of the 'Material' sub-domain shows only two outer segments ('Tabular', 'Time Series'), with the 'Language' segment missing.
- **[fatal]** Figure 6: The rendered image is a legend only and lacks the actual plot (axes, data points, or curves) required to visualize the 'Material' tradeoff mentioned in the caption.
- **[science]** Figure 6: The caption 'Material [tradeoff_legend.pdf]' appears to be a raw filename or placeholder rather than a descriptive summary of the scientific content.
- **[science]** Figure 7: The legend in the top-left scatter plot defines 'Ours' as a star symbol, but the plot displays three distinct 'Ours' variants (EywaAgent, EywaMAS, EywaOrchestra) with different colors. The legend fails to map these specific colors to the specific variants, making it impossible to distinguish them visually.
- **[science]** Figure 7: The top-left scatter plot contains a green line labeled 'Better' with an arrow pointing down-left, yet the caption claims the proposed methods achieve 'lower token consumption' (x-axis) and 'higher utility' (y-axis). The arrow direction contradicts the stated goal of maximizing utility while minimizing tokens.
- **[science]** Figure 7: The bottom-left radar chart includes a legend entry for 'Single-LLM-Agent' (pink dashed line), but the chart's title and surrounding context imply a comparison between 'Multi-LLM-Agents' and 'EywaMAS'. The inclusion of the Single-LLM-Agent baseline in this specific sub-plot is confusing and lacks clear justification in the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a tendency to introduce proprietary or metaphorical terminology without sufficient grounding for a general scientific audience. The most significant issue is the formalization of the Avatar movie concept "Tsaheylu" as a technical term for the FM-LLM interface (Section 3, "FM-LLM 'Tsaheylu' Bond"). While the analogy is illustrative, using a fictional proper noun as the primary name for a "query compiler" and "response adapter" pair is jargon that excludes readers unfamilia

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Theorem 1 (Section 3) claims strict risk improvement for EywaAgent over LLM-only agents under Assumption 1. However, the proof in Appendix A.2 relies on Assumption 4 (Performance-Preserving Interface), which asserts the interface does not degrade FM performance. The main text does not provide empirical evidence or a theoretical bound proving this interface is lossless; without this, the strict inequality in Theorem 1 is not logically guaranteed.
- **[science]** Section 4 claims EywaOrchestra strictly improves over fixed configurations (Theorem 2, Appendix A.4). The proof assumes the conductor P can achieve the oracle risk (min over configurations per task). However, the implementation uses an LLM-based planner (Section 4.2) which is a heuristic approximation. The paper does not logically bridge the gap between the theoretical oracle and the practical LLM planner to justify the claim of 'strict improvement' in the experimental results.
- **[writing]** The token complexity argument in Appendix A.5 (Proposition 3) claims EywaAgent cost is O(L_call + L_psi) while LLM-only is Theta(L(x_k)). This assumes the LLM-only agent must serialize the *entire* input x_k. However, the case study (Appendix B.2) shows the LLM agent processing a 50-point time series. If the LLM can process subsets or summaries, the Theta(L(x_k)) assumption may not hold for all tasks, weakening the logical basis for the claimed 30% token reduction.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** Theorem 1 claims 'strict risk improvement' based solely on Assumption 1 (Domain Advantage). This assumption is treated as a given fact rather than empirically validated for the specific tasks in EywaBench. The claim should be qualified as 'conditional on Assumption 1' or supported by evidence that the assumption holds for the benchmark, rather than presented as a universal guarantee.
- **[science]** Section 5 claims EywaOrchestra 'surpasses' EywaMAS on sub-domains without statistical significance testing. With only ~22 samples per sub-domain and no reported variance or p-values in Table 1, claiming superiority is an overreach. Results should be framed as 'competitive' or 'comparable' until statistical significance is established.
- **[writing]** The claim that Eywa 'reduces reliance on language-based reasoning' overstates the decoupling. The LLM still parses tasks, configures FMs, and verifies outputs. The reduction is in token volume for serialization, not in the necessity of language reasoning for orchestration. Phrasing should focus on 'reducing token overhead' rather than 'reducing reliance on reasoning'.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Add an explicit statement confirming EywaBench construction complies with source dataset licenses and introduces no new human subject data, especially for 'clinic' and 'drug' domains.
- **[writing]** Include a clear disclaimer that Eywa is not for clinical decision-making and that utility scores do not validate safety for real-world patient care in medical sub-domains.
- **[writing]** Clarify the provenance of 'gpt-5-nano' and 'gpt-5-mini'. If unreleased, replace with verifiable models to ensure reproducibility and safety auditing.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The benchmark size (N=200) is critically small for claiming 'extensive experiments' across 9 sub-domains and 3 modalities. With ~22 samples per sub-domain, statistical significance of the reported ~6-7% utility gains is unverified. Report p-values, confidence intervals, or perform a power analysis to justify the sample size.
- **[science]** The 'Single-LLM-Agent' baseline uses gpt-5-nano, but the EywaAgent baseline also uses gpt-5-nano. However, the token reduction claim (~30%) relies on the assumption that the FM call is cheaper than LLM reasoning. The paper lacks a direct ablation where the LLM-only agent is forced to process the same structured data without the FM to isolate the 'reasoning cost' vs. 'serialization cost'.
- **[science]** The theoretical claims (Theorem 1, 2) rely on Assumption 2 (Domain Advantage), which posits that FMs strictly outperform LLMs on serialized data. The paper provides no empirical validation of this assumption on the specific tasks used. Without showing that the FMs (Chronos, TabPFN) actually outperform the LLMs on the raw data tasks, the theoretical 'strict improvement' is unproven.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The benchmark size (N=200) is small for statistical significance claims. Report confidence intervals (e.g., 95% CI via bootstrapping) for the reported utility differences (e.g., the 6.6% gain) in Table 1 and Figure 1, rather than just point estimates.
- **[science]** The paper claims 'stable performance' across temperatures (Fig 3) but lacks statistical testing (e.g., ANOVA or Kruskal-Wallis) to confirm that observed variance is not significant. Add p-values or effect sizes to support robustness claims.
- **[science]** The utility metric combines sMAPE and MAAPE for time series (Eq 10). Justify the equal weighting (0.5/0.5) and provide sensitivity analysis showing how the ranking of methods changes if weights are perturbed, to ensure results are not metric-artifact dependent.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Experiments), the phrase 'We have two foundation models to build EywaAgents' is grammatically awkward. Suggest rephrasing to 'We utilize two foundation models to construct EywaAgents' for better flow and precision.
- **[writing]** In Appendix B.1 (Case Study A.1), the prompt text contains a typo: 'Please refer to Apendix' should be 'Appendix'. Additionally, the phrase 'The timestamps have been anonymized and re-indexed to avoid relying on memorized historical market trends' is slightly repetitive; consider tightening to 'to prevent reliance on memorized historical trends'.
- **[writing]** In Section 4.2 (EywaOrchestra), the sentence 'The benefit of EywaOrchestra can be understood through the gap between adaptive orchestration and any fixed configuration' is slightly vague. Consider clarifying: 'The benefit of EywaOrchestra arises from the performance gap between adaptive orchestration and any single fixed configuration'.
