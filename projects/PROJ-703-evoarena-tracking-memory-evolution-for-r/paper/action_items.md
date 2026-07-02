# Automated-review action items — EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.2 (Main Results), the text claims EvoMem improves chain accuracy by 3.7% on average. However, Table 1 shows gains of +6.1% (Terminal), +2.1% (SWE), and +3.2% (Persona). The arithmetic mean of these values is 3.8%, not 3.7%. Please verify the calculation or clarify if a weighted average was used.
- **[writing]** Section 1 (Introduction) states 'EvoMem yields an average gain of 1.5% on EvoArena' for step accuracy. Table 1 lists step accuracy gains as +2.4%, +0.4%, and +1.7%. The simple average is 1.5%, but the text does not specify if this is a simple or weighted average, which is critical given the varying instance counts across subsets (441 vs 493 vs 505).
- **[writing]** Section 3.2 claims '38.6% of milestones modify multiple files' in SWE-Chain-Evo. The text does not provide the raw count or the total number of milestones used for this calculation (stated as 145 unique milestones in the same paragraph). Please provide the numerator to allow verification of this percentage.
- **[writing]** In Section 5.1, the text states 'If patch uptake >0, gain is 8.3%; if no uptake, gain is 2.6%.' The source of these specific percentages (e.g., which subset, which model, or if this is an aggregate) is not explicitly cited or defined in the surrounding text, making the claim difficult to verify against the provided tables.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The dashed diagonal line is labeled 'step = chain', but it does not represent the line y=x (where step accuracy equals chain accuracy). The line has a positive y-intercept (approx 25%) and a slope less than 1, meaning it does not correctly visualize the condition where the two metrics are equal.
- **[writing]** Figure 1: The legend defining the 'C#' (Chain) and 'S#' (Step) tags is missing. While the caption mentions 'Step accuracy vs. chain accuracy', the specific meaning of the colored tags (e.g., C#1, S#5) attached to each model is not defined in the caption or on the figure itself.
- **[science]** Figure 3: The inner ring labels (e.g., 'Terminal-Bench-Evo 40.8%') do not match the outer ring labels (e.g., 'Software Engineering 29.21%'). The caption states the outer panels show 'question type distribution within each domain', but the outer labels appear to be domain names (like 'Software Engineering') rather than question types, creating a contradiction between the visual hierarchy and the caption's description.
- **[writing]** Figure 3: The inner ring text 'SWE-Chain Evo' is split across two lines with 'Evo' on a separate line, making it visually disjointed and harder to read compared to the other labels.
- **[writing]** Figure 4: The 'EVO - 2' panel contains a typo in the caption text 'derictory' (should be 'directory').
- **[writing]** Figure 4: The 'EVO - 1' panel contains a typo in the caption text 'post-recieve' (should be 'post-receive').
- **[science]** Figure 8: The x-axis scale is discontinuous and misleading; Panel A jumps from 30 to 70, and Panel B jumps from 200 to 500, obscuring the true density of data points and the magnitude of differences between models.
- **[writing]** Figure 8: The legend is missing; while model names are placed near points, there is no legend defining the color coding (e.g., green vs. blue vs. red) or the meaning of the point sizes.
- **[writing]** Figure 8: The y-axis label 'Accuracy (%)' is missing from Panel B, making it ambiguous if the scale matches Panel A.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology and undefined acronyms that create a barrier to entry for non-specialist readers. The most critical issue is the use of the acronyms PE, IC, and CE in the header of Table 1 (line 38) without definition in the caption or the surrounding text. While the caption defines them as "persistent environment evolution," "implicit change," and "chain evaluation," the table header itself presents them as opaque variables. This forces the reader to cro

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.2 claims an average chain accuracy gain of 3.7%, but Table 1 shows gains of +6.1%, +2.1%, and +3.2%. The arithmetic mean is 3.8%. Clarify the averaging method or correct the text to match the table data.
- **[writing]** Section 3.1 states 89 chains and 441 total instances, implying a mean length of 4.955 (rounds to 5.0), yet reports 4.96. Clarify the calculation method or correct the mean value to ensure internal consistency.
- **[writing]** Section 5.1 reports gains of 8.3% (uptake) and 2.6% (no uptake) but omits the distribution of cases. Without this, the link to the overall average gain in Section 4.2 cannot be logically verified.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The Introduction claims EvoMem improves GAIA by 6.1% and LoCoMo by 4.8%. However, Section 5.2 only reports aggregate gains on EvoArena subsets. The specific experimental setup, baseline models, and statistical significance for these external benchmark claims are missing from the main text and appendices, making the generalization to GAIA/LoCoMo unsupported by the provided evidence.
- **[writing]** The paper claims 'current agents achieve an average accuracy of 39.6% on EvoArena' (Introduction). This aggregate figure is not explicitly calculated or defined in the Results section (Section 5.2), which only lists per-subset accuracies (43.6%, 29.2%, 46.5%). The derivation of the 39.6% average (e.g., weighted by instance count vs. unweighted) is omitted, obscuring the basis of this central claim.
- **[writing]** The Conclusion states EvoMem 'improves robustness and evidence retention' generally. However, the analysis in Section 6 shows gains are highly variable (e.g., +0.4% step accuracy on SWE-Chain-Evo vs. +2.4% on Terminal). The paper over-generalizes the method's effectiveness without qualifying that benefits are domain-dependent and sometimes marginal.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader Impact' section (App. B) acknowledges privacy risks of persistent memory but lacks a concrete mitigation strategy for the 'PersonaMem-Evo' dataset, which contains synthetic health/medical and therapy-related preferences. Explicitly detail the data sanitization protocol or consent simulation used to prevent leakage of sensitive persona traits.
- **[writing]** The 'PersonaMem-Evo' construction (Sec 3.3) utilizes LLMs to generate 'therapy-related' and 'health/medical' preferences. The paper must clarify if these synthetic personas were subjected to a safety filter to prevent the generation of harmful medical advice or self-harm scenarios, and confirm that no real user data was used to seed these specific categories.
- **[writing]** The 'Terminal-Bench-Evo' and 'SWE-Chain-Evo' benchmarks involve agents executing code in evolving environments (Sec 3.1, 3.2). The paper should explicitly state the sandboxing measures (e.g., Docker isolation, network restrictions) used during evaluation to prevent agents from executing unintended dual-use actions (e.g., data exfiltration, system compromise) during the 'evolution' phases.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (p-values or confidence intervals) for the reported accuracy gains (e.g., +1.5% on EvoArena, +6.1% on GAIA). Without variance estimates or significance testing, it is unclear if these improvements are robust or due to random noise.
- **[science]** Clarify the sample size and selection method for the 'Average' rows in Table 1. Specify the exact number of models and tasks included in the average to assess the stability of the reported 1.5% gain.
- **[science]** Address potential data leakage in the PersonaMem-Evo construction. The text mentions using LLMs to generate 'implicit conversation' and 'OOD questions' from seed personas. Detail the filtering process to ensure the test questions do not contain artifacts or patterns from the generation prompts that could be exploited by the agents.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (p-values or confidence intervals) for the reported performance gains (e.g., +1.5% on EvoArena, +6.1% on GAIA). The current text presents point estimates without indicating if these improvements are statistically distinguishable from noise or baseline variance.
- **[science]** Clarify the multiple-comparisons correction strategy. With numerous benchmarks (Terminal, SWE, Persona), models, and metrics (Step vs. Chain accuracy), the risk of Type I error is high. Explicitly state if corrections (e.g., Bonferroni, Holm-Bonferroni) were applied or justify the lack thereof.
- **[science]** Define the unit of analysis and sample size (N) for the reported averages. For instance, in Table 1, is the 'Average' step accuracy a mean over 441 instances, 89 chains, or the number of agent-model combinations? The denominator for the percentages must be explicit to assess the stability of the estimates.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1, the phrase 'Difficulty: 268 medium, 152 hard, 20 easy, 1 expert' lacks a verb and reads as a fragment. Rephrase to 'The dataset difficulty distribution is: 268 medium, 152 hard, 20 easy, and 1 expert task.' to ensure grammatical completeness.
- **[writing]** Section 5.1 contains a sentence fragment: 'If patch uptake >0, gain is 8.3%; if no uptake, gain is 2.6%.' This should be integrated into a full sentence, e.g., 'When patch uptake exceeds zero, the performance gain is 8.3%, whereas it drops to 2.6% when no patches are retrieved.'
- **[writing]** In Section 5.3, the phrase 'It improves row-level evidence capture from 72.5% to 74.9%' is ambiguous regarding the subject. Clarify whether 'It' refers to EvoMem generally or the specific mechanism being discussed in that subsection to avoid confusion.
- **[writing]** The Introduction states 'EvoMem yields an average gain of 1.5% on EvoArena' but later in Section 5.2 claims 'EvoMem improves step accuracy by 2.6% and chain accuracy by 3.7% on average.' The discrepancy between the 1.5% aggregate and the specific metric gains needs clarification or consistent phrasing to prevent reader confusion.
