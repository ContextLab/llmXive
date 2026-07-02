# Automated-review action items — Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The citation 'rugg2025cognitive' (line 14) refers to a 2025 paper in Neuroscience & Biobehavioral Reviews. Verify that this specific source explicitly supports the claim that memory retrieval is an 'active and associative reconstruction process' as the primary definition, or if the authors are conflating it with older foundational work (e.g., Bartlett, Tulving) that is not cited.
- **[science]** The claim that A-Mem and Zep use 'fixed N-hop neighbor expansion' (Section 1.2) is a strong characterization. Verify that the cited papers (DBLP:journals/corr/abs-2502-12110, DBLP:journals/corr/abs-2501-13956) explicitly define their retrieval as 'fixed' and 'non-adaptive' to evidence, or if they employ any dynamic pruning that the current text overlooks.
- **[writing]** The abstract claims 'improvements up to 23%'. Table 1 shows a gain from 68.31 to 84.21 (approx 23.3%) for Gemini. However, the text states '23.3% gain' while the table values suggest a relative increase of ~23.3%. Ensure the phrasing 'up to 23%' accurately reflects the specific dataset/model combination and does not overgeneralize to all reported metrics (e.g., Claude shows 12.4%).
- **[science]** The theoretical claim that 'passive hypothesis class is strictly contained in the active hypothesis class' (Section 3.3) relies on a specific 'Binary-Tree Needle-in-a-Haystack' task. Verify that the cited logic (or the provided proof in Appendix) holds for the general case of LLM agents on natural language tasks, or if the claim is strictly limited to the constructed synthetic task.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption describes a comparison between passive retrieval and active reconstruction, but the figure displays four distinct panels (Passive Retrieval, Flat Memory, Active Reconstruction, Associative Memory). The caption fails to define or explain the 'Flat Memory' and 'Associative Memory' panels, leaving the reader to guess their relationship to the main comparison.
- **[writing]** Figure 1: The figure contains no axis labels, units, or data scales, which is acceptable for a conceptual diagram, but the lack of a formal legend defining the icons (brain vs. robot) and symbols (red X vs. green check) makes the visual encoding ambiguous without external context.
- **[writing]** Figure 2: The diagram contains three distinct panels (left, middle, right) illustrating a progression, but the figure lacks explicit labels (e.g., (a), (b), (c)) to reference these specific stages in the text or caption.
- **[writing]** Figure 2: The caption describes the figure as comparing 'passive retrieval' and 'active reconstruction', but the visual labels use '1-hop Neighbors' and 'LLM Reasoning', creating a terminology mismatch between the text and the diagram.
- **[science]** Figure 4: The x-axis labels 'CE', 'CTE', and 'CTC' in the 'No Reasoning' section are undefined; the caption mentions 'Ablation results' but does not specify what these acronyms represent, making the comparison against 'MRAgent' incomprehensible.
- **[writing]** Figure 4: The legend at the top is cut off on the right side, obscuring the label for the final bar category.
- **[science]** Figure 5: The legend labels ('Multi-hop', 'Temporal', 'Open Domain', 'Single hop') do not match the y-axis metric 'Cumulative Recall (%)', which implies a cumulative sum over turns; these categories likely represent distinct datasets or query types, but the caption fails to define what the lines represent or how they relate to the 'multi-turn reasoning' analysis.
- **[writing]** Figure 5: The legend is presented as a separate color bar below the plot rather than an integrated key, and the colors in the legend do not explicitly map to the specific lines in the plot (e.g., which color corresponds to 'Multi-hop' vs 'Single hop' is ambiguous without direct visual alignment).
- **[science]** Figure 6: The label 'Second Rejectipn' contains a spelling error ('Rejectipn' instead of 'Rejection'), which appears in both the node label and the bottom axis.
- **[science]** Figure 6: The diagram lacks explicit connecting lines or arrows between the nodes (e.g., between 'First screenplay Submission' and 'First Rejection'), making the 'reasoning trajectory' and graph structure visually ambiguous.
- **[writing]** Figure 6: The bottom axis labels ('First screenplay', 'Second screenplay', etc.) are crowded and difficult to read due to the lack of spacing or line breaks.
- **[writing]** Figure 7: The caption 'Active Memory Reconstruction' is too brief and generic; it fails to describe the specific 'Nate' example, the step-by-step reasoning process, or the timeline visualization shown in the figure.
- **[science]** Figure 7: The timeline in the third panel displays dates (01-14, 05-27, 09-29) that do not align with the textual evidence in the second panel (e1: 'last week', e3: 'just won', e4: 'last week'), creating a logical contradiction in the example's narrative.
- **[writing]** Figure 7: The final panel references 'e5' in the text ('Reference: [e4, e5]'), but the event 'e5' is never defined or shown in the preceding panels of the figure.
- **[science]** Figure 8: The x-axis labels ('call2', 'call4', 'call8') do not match the caption's description of 'per-round retrieval budget (K)'; the axis should be labeled with the specific values of K (e.g., 2, 4, 8) or the labels should be defined in the caption.
- **[writing]** Figure 8: The y-axis labels ('turn2', 'turn4', 'turn8') are ambiguous; the caption defines 'number of reasoning turns (T)', so the axis should explicitly state the values of T (e.g., 2, 4, 8) rather than using a 'turn' prefix that could be confused with a unit or category.
- **[science]** Figure 9: The text inside the bottom-left panel is truncated ('buted cortical reinst...'), making the label illegible and obscuring the comparison to the MRAgent architecture.
- **[science]** Figure 9: The diagram lacks a legend or explicit labels defining the specific icons (eye, ear, robot, question marks) and their functional mapping between the biological and computational domains.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript demonstrates a strong command of the specific sub-field of LLM agents and memory systems, but it occasionally relies on jargon that creates unnecessary friction for a broader audience. First, the term engrams appears in Section 1 ("cues trigger engrams") without definition. While central to the cognitive neuroscience motivation, a non-specialist reader may not know this refers to the physical representation of a memory. A brief parenthetical definition would bridge this gap. Secon

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Theorem 1 assumes the active agent can perfectly read path bits in a binary-tree task. The paper fails to justify that the proposed LLM routing mechanism ($f_{select}$) can reliably perform this bit-extraction in noisy, real-world data, creating a gap between the theoretical proof and the practical claim of superiority.
- **[science]** The claim that active reconstruction reduces token costs (Section 5.2) lacks a breakdown of reasoning vs. retrieval tokens. The algorithm requires multiple LLM calls per step; without evidence that pruning savings outweigh this overhead, the causal link between the active mechanism and lower cost is unsupported.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that MRAgent reduces 'runtime costs' is over-claimed. Table 2 shows MRAgent (586s) is slower than Mem0 (533s). The text implies universal reduction, but data only supports reduction vs. specific graph baselines like A-Mem. Clarify this limitation.
- **[science]** Theorem 1 claims active retrieval is 'strictly more powerful' based on a binary-tree separation task. The paper does not prove LoCoMo/LongMemEval queries match this worst-case structure. Attributing empirical gains directly to this theorem risks over-extrapolating the theoretical result to the specific dataset.
- **[science]** Table 2 claims 118k tokens includes 'construction and retrieval.' Given MRAgent's multi-step active reconstruction (Algorithm 1), this count seems low. Clarify if construction costs are amortized or excluded, as the 'on-demand' efficiency claim may be misleading if baselines are compared differently.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Impact Statement (Section 7) acknowledges privacy risks but lacks specific mitigation strategies for the proposed 'active reconstruction' mechanism. Since the agent autonomously infers new cues and traverses memory graphs, it may inadvertently expose sensitive user data not explicitly queried. The authors should detail how the system prevents over-exposure of private information during the multi-step reasoning process.
- **[writing]** The paper relies on LLM-based distillation to populate the memory graph (Section 3.3, Appendix A.1) without mentioning human-in-the-loop verification or consent protocols for the source dialogue data. If the system is deployed in real-world settings, the automatic extraction of 'semantic aspects' and 'episodic events' from user conversations raises significant consent and data governance concerns that require explicit discussion.
- **[writing]** The 'Binary-Tree Needle-in-a-Haystack' theoretical task (Appendix A.4) and the 'Case Study' (Appendix A.5) use synthetic or anonymized examples. However, the paper does not address the potential for the active reconstruction mechanism to hallucinate or fabricate 'cues' that could lead to the retrieval of false or harmful information about real users in a production environment. A discussion on the safety of the inference path is needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Theoretical claims (Theorem 1, Sec 3.3) assert strict superiority of active over passive retrieval but rely on a synthetic 'Binary-Tree Needle-in-a-Haystack' task. The paper lacks empirical evidence that this theoretical separation translates to the complex, noisy distributions of LoCoMo/LongMemEval. Re-run experiments with a controlled ablation where baselines are given oracle access to the 'correct path' to isolate the value of the reconstruction mechanism itself.
- **[science]** Statistical significance is not reported for the main results in Table 1 (LoCoMo) or Table 2 (LongMemEval). Given the large performance gaps (e.g., 23% gain), standard error bars or p-values from multiple random seeds are required to rule out variance or specific seed bias, especially since baselines like Mem0 show high variance across categories.
- **[science]** The cost analysis (Table 2) claims MRAgent reduces token consumption to 118k vs 632k for A-Mem. However, the 'Active Reconstruction' process involves iterative LLM calls (Algorithm 1, lines 4-10) which typically increase token usage. The paper must explicitly detail how the 'on-demand' pruning offsets the overhead of multi-step reasoning to achieve this net reduction, or provide a breakdown of tokens per step.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Table 2 report point estimates (e.g., 84.21, 90.19) without measures of statistical uncertainty (standard deviation, standard error, or confidence intervals). Given the use of LLM backbones which can exhibit stochastic variance, the authors must report results over multiple seeds or provide confidence intervals to substantiate the claimed improvements.
- **[science]** The paper claims significant improvements (e.g., 23.3% gain) but does not report the results of statistical significance tests (e.g., paired t-tests, Wilcoxon signed-rank) comparing MRAgent against the strongest baselines. Without p-values or effect sizes, it is unclear if the observed gains are statistically distinguishable from random variance.
- **[science]** The ablation study (Figure 3) and budget sensitivity analysis (Figure 4) present performance trends but lack error bars or statistical validation. The authors should clarify if these curves represent single runs or averages, and whether the observed monotonic improvements are statistically significant.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Experiments), the text references 'Figure 5' and 'Figure 6' (e.g., 'Figure 5 shows...'), but the provided LaTeX source only contains labels for figures up to Figure 4 (e.g., fig:ablation, fig:fig_multi_turns). Ensure all figure references match the actual labels defined in the source to prevent broken links in the compiled PDF.
- **[writing]** The abstract claims 'improvements up to 23% over strong baselines,' but the main text (Section 5) states a '23.3% gain' on Gemini and '12.4% on Claude.' The abstract should be precise (e.g., 'up to 23.3%') or clarify that the 23% figure refers specifically to the Gemini backbone to avoid ambiguity.
- **[writing]** In the Appendix, Table 1 (tab:tools) and Table 2 (tab:tools) appear to be duplicates with slightly different formatting. Ensure that the appendix does not contain redundant tables that confuse the reader, or merge them if they serve the same purpose.
