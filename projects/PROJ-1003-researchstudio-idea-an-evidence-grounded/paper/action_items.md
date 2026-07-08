# Automated-review action items — ResearchStudio-Idea: An Evidence-Grounded Research-Ideation Skill Suite from ML Conference Outcomes

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** The paper's central empirical claims rely entirely on a timeline and model ecosystem that does not exist. The evaluation section (Section 5) compares the proposed "IdeaSpark" system against "GPT-5.5" and "Opus-4.8". As of the current real-world date, neither of these models exists; the latest public versions are GPT-4o and Opus 3.5/4.0. The bibliography lists these as 2026 publications, and the text references "ICLR 2026" seeds and outcomes. This creates a fatal claim-accuracy failure: the paper

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption describes a 'Left' and 'Right' panel, but the rendered image contains only the Left panel (quality-novelty trade-off). The Right panel (mean idea-quality across 21 domains) is missing.
- **[science]** Figure 1: The caption states the plot shows a trade-off over '100 ICLR-2026-Oral seeds', yet the visualization displays single points with ellipses for each method, which typically represent a single aggregate mean and variance rather than a distribution of 100 individual seeds.
- **[science]** Figure 3: The legend defines 'Oral-safe (6)' and 'Reject-warn (1)', but the y-axis labels for clusters C21 and C09 are colored red (Reject-warn) instead of green (Oral-safe), contradicting the caption's claim that six clusters clear the Oral threshold and the legend's color coding.
- **[writing]** Figure 3: The legend title 'cluster label color' is ambiguous; it should explicitly state 'Cluster label risk flag' to distinguish it from the bar colors (Reject, HC, Oral) shown in the bottom right.
- **[science]** Figure 4: The caption claims '31 clusters, colored' but the plot lacks a legend mapping the ~31 distinct colors to specific cluster identities or labels, rendering the visualization uninterpretable.
- **[writing]** Figure 4: Axis tick labels (e.g., -2, -1, 0) are rendered in a very light gray that is nearly illegible against the white background.
- **[writing]** Figure 5: The caption text is truncated mid-sentence at the end ('...while the segment'), leaving the description of the middle ring incomplete.
- **[science]** Figure 5: The outer ring is labeled 'Oral acceptance rate' in the image, but the legend defining the color scale (dark vs. light gray) is missing from the rendered figure, making the data illegible.
- **[writing]** Figure 6: The x-axis labels are rotated 45 degrees and overlap significantly, making them difficult to read; consider horizontal alignment or reducing label density.
- **[writing]** Figure 6: The y-axis labels are truncated on the left side of the plot area, cutting off the beginning of several pattern names (e.g., 'Reframe as a Solvable Object').
- **[science]** Figure 7(b): The caption claims each curve is a probability mass function summing to 100%, but the y-axis is labeled '% within class' and the data points (e.g., Oral at k=2) are clearly below 100% (approx. 60%), indicating the curves do not sum to 100% as described.
- **[writing]** Figure 7(b): The y-axis label '% within class' is ambiguous; it should explicitly state 'Percentage of papers within class' or similar to clarify that the values represent the distribution of k for each class.
- **[writing]** Figure 8: The caption contains LaTeX formatting artifacts (e.g., '$n 20$', '$n 10$') that likely indicate missing inequality symbols (e.g., $n \ge 20$), making the inclusion criteria for the bars unclear.
- **[writing]** Figure 8: The y-axis labels are multi-line text strings that are difficult to read; using a legend or a more compact label format would improve legibility.
- **[science]** Figure 9: The caption states 'Diamonds show $\Delta_{OH}$ where $n_{HC} \ge 5$', but the legend defines the diamond symbol simply as '$\Delta_{OH}$ (Oral-HC share)' without the sample size constraint. This creates a discrepancy between the visual legend and the caption's filtering criteria.
- **[writing]** Figure 9: The caption contains LaTeX formatting artifacts (e.g., '\(_OR\)', '\(n_HC 5\)') that are not rendered as readable text or mathematical symbols, making the definitions of the bars and diamonds difficult to parse.
- **[science]** Figure 10: The caption states that gray cells in panel (b) indicate $n_O + n_R < 5$ (too few papers), but the colorbar explicitly includes a value of 0. This creates a contradiction where a cell with 0% Oral rate (valid data) is visually indistinguishable from a cell with missing data (gray).
- **[writing]** Figure 10: The x-axis labels (ideation patterns) are rotated 45 degrees but are still too crowded and overlap significantly, making them illegible without zooming in.
- **[science]** Figure 11: The x-axis scale (0 to 25) contradicts the caption's claim that patterns touch '>= 18 domains' and the visual bars which extend past 25; the axis appears to represent paper counts (matching the bar labels) rather than the number of distinct domains.
- **[writing]** Figure 11: The x-axis label ('# distinct domains with >= 5 papers') is misleading because the axis tick marks (0, 5, 10, 15, 20, 25) do not align with the data values shown in the bar annotations (e.g., 527, 1008), suggesting the axis is scaled for paper counts, not domain counts.
- **[writing]** Figure 12: The caption contains a LaTeX rendering artifact 'k 230%' which should be formatted as '$k \ge 30\%$' or similar to be readable.
- **[writing]** Figure 12: The legend text in the left panel is extremely small and dense, making pattern names like 'Decompose for Differentiated Treatment' difficult to read.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper is generally well-structured for a technical audience, but it relies on several undefined acronyms and symbols that would stall a competent reader from an adjacent field (e.g., a statistician or a researcher in a different ML subfield). The most significant issue is the introduction of the symbol $\Delta_{\text{OH}}$ in Section 5.1. The text defines $\Delta_{\text{OR}}$ clearly but leaves $\Delta_{\text{OH}}$ undefined until a later paragraph where the formula is given, but the symbol

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Clarify the logical link between 'unclustered' papers (Sec 5.2) and '100% coverage' (Sec 6.1). If 902 papers lack a cluster, how are they assigned to the 15 patterns? Explicitly state the assignment mechanism for unclustered papers to justify the 100% coverage claim.
- **[writing]** Refine the phrasing in Sec 7.1: '11/15 patterns receive Reject-only mapping' is ambiguous. Specify that 11 patterns contain *at least one* cluster unique to the Reject-only run, rather than implying the patterns themselves are exclusive to rejections.
- **[writing]** Clarify the 'held-out' claim in Sec 10. Since seeds are from 2026 and corpus ends in 2025, specify that this tests temporal generalization to future data, not just random sampling from the same distribution.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Intro: Claim 'IdeaSpark produces stronger proposals' implies general superiority, but Section 7 shows GPT-5.5 wins on Novelty (3.73 vs 2.92). The text frames this as a 'misleading' failure mode rather than a trade-off. Rephrase to 'improves quality scores while maintaining competitive novelty' to match the data showing a clear quality/novelty trade-off.
- **[writing]** Conclusion: States 'success/failure conditions can be packaged into skills' as an established fact. Section 7 notes 'human review is pending' and evaluation relies on automated judges. The claim that conditions are successfully 'packaged' is not yet licensed. Add 'preliminary' or 'in automated evaluation' to the claim, or state human validation is required to confirm efficacy.
- **[writing]** Section 1 (Main findings): Claim 'patterns are domain-conditional' is supported only by variance in Oral rates within the ML corpus (Fig 4). The text does not acknowledge that this effect is untested outside ICLR/ICML/NeurIPS. Add a limitation noting that 'domain-conditional' effects are observed only within the ML conference corpus and may not generalize to other scientific fields.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a methodological analysis of ML conference outcomes to derive "ideation patterns" for research idea generation. From a safety and ethics perspective, the work is low-risk. The dataset consists of publicly available metadata and abstracts from major ML conferences (ICLR, ICML, NeurIPS), which does not involve human subjects, PII, or sensitive personal data requiring IRB approval. The methodology (clustering, pattern induction) and the resulting "skill suite" (IdeaSpark) are designed to assist in scientific ideation, not to generate harmful content, deceive users, or automate cyber/physical attacks.

While the paper discusses "exploits" and "attacks" in the context of analyzing why certain papers were rejected (e.g., in the appendix example for "Audit and Pivot"), these are described as abstract failure modes of research strategies, not operational instructions for generating real-world vulnerabilities. The paper explicitly scopes its use as an "ideation scaffold" and includes a "Responsible Use" section (Section 13) acknowledging these boundaries. There are no undisclosed conflicts of interest, license violations regarding the public data used, or fairness harms to identifiable groups. The risk of dual-use is negligible as the output is high-level research strategy, not executable code or specific attack vectors. No specific safety disclosures or mitigations are missing.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The paper presents a compelling narrative for deriving research ideation patterns from conference outcomes, but the experimental design contains significant gaps that prevent the evidence from fully supporting the central claims, particularly regarding the efficacy of the "IdeaSpark" skill suite. First, the primary evaluation of the generated ideas (Section 9, Tables 4 & 5) relies entirely on automated LLM judges. While the paper reports standard deviations, these are derived from the 100 seeds,

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 3 reports 'std' for quality scores but does not specify if this is SD across seeds or SE. Report the 95% CI for the mean quality score (3.87) or clarify the metric to allow assessment of stability.
- **[writing]** Tables 4-6 report percentages to one decimal place for small samples (n<30), implying false precision. Round to integers or report exact counts (e.g., 17/20) to prevent misinterpretation of stability.
- **[writing]** Section 4.2 and 8 use silhouette scores to claim 'construct validity' of clusters. Clarify that silhouette is a heuristic for density, not semantic validity, and consider adding a stability metric (e.g., bootstrap consistency) to support the 15-pattern claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the prose is dense but largely clear. The logical flow from data collection to pattern induction and finally to the skill suite is coherent. However, there are several instances where sentence structure or paragraph organization creates minor friction for the reader. In Section 1.4, the "Main empirical findings" subsection mixes a positive result with a limitation ("human review is pending") in the same list item. This dilutes the impact of the automate
