# Automated-review action items — Heterogeneous Scientific Foundation Model Collaboration

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim that EywaAgent improves utility by ~7% (Intro) conflicts with Table 1 (6.6%). Align text to 'approx 6.6%' or justify rounding to avoid over-claiming.
- **[science]** Theorem 1 claims strict risk improvement based on Assumption 1, but the paper does not empirically verify that the specific FMs (Chronos, TabPFN) satisfy this strict inequality on EywaBench tasks. Clarify this dependency.
- **[writing]** Section 5.3 claims EywaOrchestra 'surpasses' EywaMAS. Table 1 shows lower overall utility (0.6746 vs 0.6761). Clarify that gains are cost-based or limited to specific sub-domains to avoid misleading readers.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 3: The caption claims distributions are 'near-uniform,' but the data shows a 1.8x range (15 to 28 samples) with no visual indication of statistical uniformity or error margins.
- **[writing]** Figure 3: The y-axis label '# Samples' is ambiguous; it is unclear if these are raw counts or normalized percentages, which is critical for evaluating the 'uniformity' claim.
- **[writing]** Figure 5: The caption contains a formatting artifact '$$' between 'nine sub-domains (inner ring)' and 'three modalities (outer ring)' which should be corrected to standard punctuation.
- **[science]** Figure 5: The caption claims 'All 27 cells are populated' (9 sub-domains x 3 modalities), but the 'Material' sub-domain in the inner ring only displays two outer segments ('Tabular' and 'Time Series'), missing the 'Language' segment.
- **[fatal]** Figure 6: The rendered image is a legend only and lacks the actual plot (axes, data points, or curves) required to visualize the 'Material' tradeoff mentioned in the caption.
- **[science]** Figure 6: The caption 'Material [tradeoff_legend.pdf]' appears to be a raw filename or placeholder rather than a descriptive summary of the data presented.
- **[science]** Figure 7: The legend defines 'Single-LLM-Agent' with a pink dashed line, but the scatter plot uses pink circles for this method, creating a symbol mismatch.
- **[science]** Figure 7: The legend defines 'Multi-LLM-Agent' with a green dashed line, but the scatter plot uses green circles for this method, creating a symbol mismatch.
- **[science]** Figure 7: The legend defines 'EywaOrchestra (Ours)' with a pink star, but the scatter plot uses a purple star for this method, creating a symbol mismatch.
- **[writing]** Figure 7: The legend for 'EywaOrchestra (Ours)' is positioned outside the plot area and is visually disconnected from the other legend entries.
- **[writing]** Figure 7: The legend for 'Multi-LLM-Agent' is positioned outside the plot area and is visually disconnected from the other legend entries.
- **[writing]** Figure 7: The legend for 'Single-LLM-Agent' is positioned outside the plot area and is visually disconnected from the other legend entries.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'FM' (Foundation Model) at first use in Section 2. Currently, the text jumps to 'Domain-Specific Foundation Model ("FM")' without explicitly stating that FM is the acronym for the broader class before narrowing the scope.
- **[writing]** Replace the metaphor-heavy term 'Tsaheylu' with a standard technical descriptor (e.g., 'bidirectional interface' or 'modality bridge') in the main text. While the Avatar analogy is creative, using a fictional proper noun as a primary technical term for a communication protocol creates unnecessary cognitive load for non-fans and non-specialists.
- **[writing]** Define 'MAS' (Multi-Agent Systems) at first use in Section 2. The text introduces 'Multi-Agent Systems (MAS)' but later uses 'EywaMAS' and 'MAS' interchangeably without ensuring the acronym is clearly established as a standard term before the specific framework name.
- **[writing]** Replace 'modality-native' with 'native-modality' or 'native to the modality' in Section 1 and 3. The hyphenated adjective 'modality-native' is non-standard jargon that obscures meaning; 'native to the modality' is clearer.
- **[writing]** Define 'MCP' (Model Context Protocol) at first use in Section 3. The text states 'Model Context Protocol (MCP)' but assumes the reader knows this is a specific protocol standard rather than a generic description. If it is a specific external standard, it should be cited or briefly explained for non-LLM-specialists.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Theorem 1 (Improvement of EywaAgent) claims strict risk reduction under Assumption 1 (Domain Advantage). However, the proof in Appendix A.3 relies on Assumption 4 (Performance-Preserving Interface) to ensure the interface does not degrade FM performance. The main text does not explicitly state that Assumption 4 is a necessary condition for Theorem 1, creating a logical gap where the conclusion might not hold if the interface introduces significant noise or translation error.
- **[science]** The claim that EywaOrchestra 'approaches EywaMAS with lower cost' (Section 5.3) relies on the conductor selecting the optimal configuration. However, the experimental setup states the conductor is an LLM mapping tasks to a finite pool. The paper does not provide evidence that the LLM conductor achieves near-oracle selection rates; without this, the logical link between 'adaptive orchestration' and 'lower cost' is weak, as a poor conductor could select suboptimal, high-cost configurations.
- **[writing]** The token complexity argument (Proposition 2, Appendix A.6) assumes $L(x_k) \gg L_{call} + L_{\psi}(o_k)$. While true for raw data, the LLM must still parse the task description and format the output. The paper claims a ~30% token reduction but does not logically isolate the savings from the FM delegation versus the overhead of the orchestration logic, making the causal claim of 'reduced reliance on language-based reasoning' partially unsupported by the provided metrics.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** Theorem 1 (0_sections/3_eywaagent.tex) claims 'strict risk improvement' based on Assumption 1, which asserts FMs are strictly better than *any* LLM on serialized data. This is an unproven universal claim ignoring multimodal LLMs. The theorem proves a tautology (if A>B then A>B) rather than demonstrating the framework's actual advantage. Reframe as conditional on specific FMs used.
- **[writing]** The paper claims Eywa 'avoids explicit token-level reasoning' (0_sections/3_eywaagent.tex). However, the LLM still performs the 'query compiler' and 'response adapter' steps, which inherently involve language reasoning. The claim of 'avoiding' language reasoning is an overstatement; the system shifts computation burden but still relies on language for orchestration. Clarify to avoid implying the LLM is bypassed.
- **[science]** The 'strict inequality' in Theorem 1 assumes the 'Tsaheylu' interface is perfectly faithful (Appendix 1_appendix/theoretical_analysis.tex). In practice, serialization errors are non-zero. Claiming 'strict' improvement without bounding interface error overstates the guarantee. The proof should acknowledge improvement is only strict if interface overhead does not negate domain advantage.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript lacks an explicit statement regarding Institutional Review Board (IRB) or ethics committee approval for the construction of EywaBench, particularly given its derivation from human-generated datasets (MMLU-Pro, DeepPrinciple). While the data is public, the aggregation and potential re-identification risks in the new benchmark schema should be addressed in the Ethics or Data Availability section.
- **[writing]** The paper claims to use 'gpt-5-nano' and 'gpt-5-mini' (Section 5.2, Appendix A.1). As these model versions do not currently exist in public APIs, this raises concerns regarding the reproducibility of the safety evaluation and the potential for hallucinated results. The authors must clarify the exact model versions used or provide a path to reproduce the specific API calls.
- **[writing]** The 'Case Study A' (Appendix) demonstrates the system's ability to predict financial signals (NASDAQ). The authors should explicitly discuss the dual-use risk of this capability, specifically the potential for automated market manipulation or high-frequency trading strategies that could harm market stability, and include a mitigation statement in the Limitations or Discussion section.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The benchmark size (N=200) is critically small for claiming 'extensive experiments' across 9 sub-domains and 3 modalities. With only ~22 samples per sub-domain, statistical significance of the reported ~6-7% utility gains is unverifiable without confidence intervals or p-values. The paper must report variance metrics (std dev) and statistical tests to support the claim that gains are not due to sampling noise.
- **[science]** The 'Single-LLM-Agent' baseline uses gpt-5-nano, but the text mentions evaluating 'other models from and beyond the GPT family' without presenting comparative data for non-GPT baselines in the main tables. To validate the claim that Eywa improves over 'language-only baselines' generally, results for at least one non-GPT baseline (e.g., Gemini or Claude) must be included in Table 1.
- **[science]** The theoretical claim of 'strict risk improvement' (Theorem 1) relies on Assumption 2 (Domain Advantage), which posits that FMs strictly outperform LLMs on serialized inputs. The empirical section does not explicitly validate this assumption by comparing the raw performance of Chronos/TabPFN against the LLM on the serialized inputs in isolation. A dedicated ablation showing the FM-only vs. LLM-only performance on the domain-specific component is required to ground the theoretical claims.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The benchmark size (N=200) is insufficient for robust statistical inference across 9 sub-domains and 3 modalities. With ~22 samples per sub-domain, the standard error for mean utility is high. Report confidence intervals (e.g., 95% CI via bootstrapping) for all main results in Table 1 and Figure 1 to quantify uncertainty.
- **[science]** The paper claims 'statistically significant' improvements (e.g., 6.6% utility gain) but provides no hypothesis testing results (p-values, effect sizes, or power analysis). Explicitly state the statistical test used (e.g., paired t-test, Wilcoxon signed-rank) and report p-values for all key comparisons against baselines.
- **[science]** The utility metric combines exact match, numeric error, and lexical similarity (Appendix Eq 1-3). The aggregation weights (alpha=0.6, beta=0.4) and the cap (tau=0.8) are arbitrary. Provide a sensitivity analysis showing how results change if these hyperparameters are varied, or justify them with a validation study.
- **[science]** The benchmark composition (Table 1 in Appendix) shows uneven sample counts per sub-domain (15-28). The reported 'mean utility' is an unweighted average. Clarify if this is appropriate given the imbalance, or provide a weighted average based on domain prevalence to avoid bias.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Experiments), the phrase 'We have two foundation models to build EywaAgents' is grammatically awkward. Suggest revising to 'We utilize two foundation models to construct EywaAgents' for better flow and precision.
- **[writing]** In Appendix A.2 (Case Study A.2), the heading 'Why Not Directly Use the Foundation Model?' is a question fragment. For consistency with academic style, consider changing to a declarative statement like 'Limitations of Direct Foundation Model Usage' or 'Rationale for the Tsaheylu Interface'.
- **[writing]** In Section 5 (Experiments), the sentence 'We use gpt-5-nano as the default language model and we also evaluate other models from and beyond the GPT family in our later experiments' contains a redundant 'and we'. Suggest removing the second 'and' to improve conciseness: '...and also evaluate other models...'.
