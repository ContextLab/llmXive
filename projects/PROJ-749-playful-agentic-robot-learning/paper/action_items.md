# Automated-review action items — Playful Agentic Robot Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The abstract and Section 1 claim RoboSuite transfer improves performance by 8.9 points. Table 3 shows the average gain is +8.9 pp (40.3% to 49.1%), but the 'Two-arm handover' task shows a -4.0 pp decrease. The text should clarify that the 8.9 pp is an average across tasks, not a uniform improvement, to avoid implying every task improved.
- **[science]** Section 3.2 defines the Competence Frontier F(tau) as peaking at r_bar approx 0.5. However, the text states r_bar is the 'average Wilson-bounded empirical success rate'. Wilson bounds are typically used for confidence intervals on proportions, not as a direct point estimate for the mean success rate in a formula. The authors should clarify if r_bar is the raw empirical mean or the lower bound of the Wilson interval, as this changes the mathematical interpretation of the 'peak' at 0.5.
- **[writing]** The bibliography lists 'fu2026capx' (CaP-X) with a 2026 publication year. As this is a preprint review, citing a future-dated paper (2026) as an established reference for 'CaP-X shows multi-turn feedback benefits' is factually premature unless the paper is already publicly available under that specific citation key. The authors should verify the citation status or adjust the year to the actual arXiv submission date.
- **[writing]** Table 3 reports 'Two-arm lifting' success as 5/50 (10.0%) for CaP-Agent0 and 17/50 (34.0%) for RATs. The delta is listed as +24.0 pp. However, 34.0 - 10.0 = 24.0. The text in Section 5.2 claims 'Notable gains: ... two-arm lifting (+24.0 pp)'. This is mathematically correct, but the table also lists 'Two-arm handover' with a -4.0 pp delta. The text should ensure the 'notable gains' list does not inadvertently imply all transfer tasks improved, given the handover failure.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption 'Qualitative comparisons in simulation' is too generic and does not describe the specific tasks (e.g., 'open the drawer', 'turn on the stove') or the methods being compared (CaP-Agent0 vs. RATs) shown in the image.
- **[writing]** Figure 1: The task labels on the left include dataset names in parentheses (e.g., '(MolmoSpaces)', '(LIBERO-PRO)'), but the caption does not define these terms or explain their relevance to the simulation environment.
- **[science]** Figure 2: The caption claims to show 'sim-to-real transfer' results, but the image displays four rows of real-world robot execution sequences (Place Cube, Swap Cubes, Close/Open Drawer) without any corresponding simulation baselines or side-by-side comparisons to demonstrate the transfer.
- **[writing]** Figure 2: The image contains no figure number, title, or caption text embedded within the visual itself, relying entirely on external placement which is not visible in the provided render.
- **[science]** Figure 7: The left panel ('Skill library') is a stacked area chart where the y-axis represents the cumulative total of all categories. However, the legend labels ('Verified', 'Experimental', 'Deprecated') imply these are separate series. The visual representation makes it impossible to read the specific count of 'Verified' skills (the bottom dark band) without estimating the height of the band itself, which is obscured by the bands above it. A line plot or bar chart would be clearer for comparin
- **[writing]** Figure 7: The caption states the figure reports 'verified/experimental/deprecated skill counts', but the left plot's y-axis is labeled 'Learned helpers'. While likely synonymous in context, the terminology mismatch between the axis label and the caption/legend creates ambiguity.
- **[science]** Figure 8: The caption states 'Each column aggregates 100 evaluation trials,' but the 'Pick' column sums to 846 calls (714+0+97+139+0), which is inconsistent with the stated trial count or implies a misunderstanding of how 'calls' vs 'trials' are aggregated.
- **[writing]** Figure 8: The heatmap cells contain two numbers (count and percentage) stacked vertically without explicit labels or delimiters, which forces the reader to infer which is which based on the caption; adding a legend or distinct formatting (e.g., bold for count) would improve clarity.
- **[science]** Figure 12: The caption claims the figure shows 'LIBERO-to-RoboSuite skill transfer' and that RATS succeeds by 'reusing skills selected from a LIBERO-derived library,' but the figure itself contains no visual evidence of the LIBERO source, the library contents, or the specific skills being reused; it only shows a generic 'Success' state.
- **[writing]** Figure 12: The figure is a single static image showing a 'Success' state, but the caption implies a comparison ('direct code synthesis fails while RATS succeeds') that is not visually represented in the provided image (e.g., no 'Failed' panel or side-by-side comparison).

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific jargon and undefined acronyms, which creates a barrier for readers outside the immediate sub-fields of robotics and intrinsic motivation. First, the term Code-as-Policy is introduced in the Abstract and Introduction as a central concept but is never explicitly defined. While the title suggests it involves code, the specific mechanism (using LLMs to synthesize executable programs for control) should be briefly explained upon first mention to aid no

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling framework for 'Playful Agentic Robot Learning' using the RATs system. The logical flow from the problem statement (task-driven limitations) to the proposed solution (self-directed play with skill distillation) is generally sound. However, there are specific areas where the causal claims and definitions require tighter logical consistency to fully support the conclusions. First, the claim of transfer "without finetuning" (Abstract, Sec 1) creates a logical tension

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims regarding the autonomy and generalization of the \textsc{RATs} system that appear to exceed the evidence provided in the text. First, the Abstract and Section 5.3 claim that skills transfer to real-world tasks "without finetuning." While the authors state they do not finetune the LLM, the claim implies a level of zero-shot generalization that is not fully supported. The real-world evaluation (Table 3) shows modest gains (+8.8 pp), but the paper does not clarify if

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript addresses safety and ethics primarily through a brief, high-level statement in Section 1 ("Safety Considerations") and a mention of a "Quality Checker" agent in the methodology. While the authors cite ISO 10218 and ISO 15066, the review finds the current treatment of safety insufficient for a system involving autonomous, self-directed code generation and physical robot interaction. First, the "Safety Considerations" section (Section 1) is too generic. It lists compliance standards

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations) for the reported percentage point improvements (e.g., +20.6 pp in LIBERO-PRO). The current tables present single-point averages without variance metrics, making it impossible to assess if gains are robust or due to random seed variance.
- **[science]** Clarify the random seed protocol. The reproducibility checklist mentions 'Fixed seeds (42)', but LLM-based agents often exhibit high variance even with fixed seeds due to non-deterministic sampling or environment stochasticity. Report results averaged over multiple seeds (e.g., 3-5) with standard deviation to validate the stability of the +17.0 pp gain in MolmoSpaces.
- **[science]** Provide a more rigorous control for the 'compute-matched' baseline in Table 5. The comparison between a 15-turn baseline and the play-learned model needs to explicitly account for the variance in the 15-turn baseline. If the 15-turn baseline was only run once, the comparison is statistically weak.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The manuscript presents compelling empirical results for the \textsc{RATs} framework, but the statistical rigor of the analysis requires strengthening to support the quantitative claims. First, the primary results tables (Table 1: LIBERO-PRO, Table 2: MolmoSpaces, Table 3: RoboSuite/Real-World) report success rates as single-point percentages (e.g., 43.8%, 38.0%). In experimental robotics and machine learning, reporting point estimates without measures of uncertainty (standard deviation, standar

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Related Work), the phrase 'Play and Curiosity' is used as a bolded header, but the subsequent paragraph begins with 'Play provides...' without a clear transition. Consider rephrasing the opening sentence to better integrate with the header or add a brief introductory clause to improve flow.
- **[writing]** In Section 3.2 (Task Proposer Team), the formula for Competence Frontier F(tau) is presented with a parenthetical explanation of r-bar. The sentence structure is slightly dense. Consider breaking this into two sentences or using a colon to separate the definition from the explanation for better readability.
- **[writing]** In Section 5.2 (Cross-Environment Transfer), the phrase 'Notable gains: cube lifting (+16.0 pp), two-arm lifting (+24.0 pp).' is a sentence fragment. While common in technical writing, it could be integrated into a full sentence (e.g., 'Notable gains include...') to maintain consistent grammatical structure with the surrounding text.
- **[writing]** In the Appendix, Section A.4 (Agent Prompts), the prompt templates use a mix of natural language and code blocks. Ensure that the transition between the 'SYSTEM PROMPT' and 'USER TEMPLATE' sections is clear, perhaps by adding a brief explanatory sentence before the code block to guide the reader.
