# Automated-review action items — AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a well-structured argument for a bounded-memory contract, and the internal consistency of the reported results (e.g., the 3/10 vs 6/10 win rates and the corresponding statistical tests) is generally sound. The authors are transparent about the directional nature of their findings and the limitations of their sample size. However, there are significant factual claims regarding the specific models used as baselines that cannot be verified against the public record. The paper rep

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a broken cross-reference ('are given in --') instead of citing the specific figure or section containing the exact numbers and caveats.
- **[writing]** Figure 1: The 'L1 protocol' through 'L5 skills' labels in the bottom-left panel are not defined in the caption, leaving the specific meaning of these layers ambiguous to the reader.
- **[writing]** Figure 2: The caption states that summary labels (e.g., 'no trade-off', token-efficiency, score-gap figures) are illustrative, but the figure itself displays these specific claims as definitive facts (e.g., '90%+ fewer tokens', '+52.4 vs best public') without visual distinction, potentially misleading readers about the data's status.
- **[science]** Figure 2: Panel (c) presents a box plot for 'Ours +L5 scaffold' with n=30, while other groups (AGI-Eval GPT-5.4, Opus 4.7) have n=9; the caption notes sample size differences but does not explicitly warn that the visual comparison of distributions across these disparate sample sizes is statistically limited.
- **[writing]** Figure 3: The legend in panel (a) displays the formula as '1/4 O(c^2)', but the caption describes the counterfactual as '1/4 of naive O(c^2) growth' with a specific median token formula; the legend notation is ambiguous and should explicitly state it represents the total cumulative growth curve to match the y-axis.
- **[writing]** Figure 3: The x-axis label 'strategic decisions c' is present, but the caption refers to 'ten fixed-A0 runs' and 'two per cell' without explicitly defining what the specific x-axis values (0 to 140) represent in the context of the 'Per-run growth' panel (e.g., is it the max decisions reached in a run?).
- **[science]** Figure 4: The diagram labels the transition from 'mode-a' to 'mode-b' as 'swap L5 source', but the visual content shows 'L5 human' (mode-a) changing to 'L5 agent' (mode-b). The caption defines the comparison as isolating 'L5 source', yet the diagram does not explicitly label 'human' and 'agent' as the specific sources being swapped, creating ambiguity about the ablation axis.
- **[writing]** Figure 4: The caption states 'adjacent bars are organized by a named ablation axis', but the figure is a schematic flowchart of configuration states, not a bar chart. This terminology mismatch between the caption and the visual representation is confusing.
- **[science]** Figure 5: The x-axis labels 'A2', 'A3', 'A4', 'A5', 'A7', 'A8' are undefined; the caption does not explain what these codes represent or how they relate to the named conditions (e.g., 'baseline-strict', 'Mode B').
  - severity: science
    text:
- **[science]** Figure 5: The 'Mode B' and 'full+postrun' groups lack sample size (n) labels, whereas all other groups explicitly state '(n=...)', preventing assessment of statistical reliability for these key conditions.
summary:
- **[writing]** Figure 6: The caption ends abruptly with 'e [fig_cmp_strips.pdf]', cutting off the explanation of the token convention (likely 'estimated') and leaving the sentence incomplete.
- **[science]** Figure 6: The y-axis for (c) Cost is labeled 'Fresh tokens / score pt' with a log scale, but the data labels (e.g., '570.7k') are placed directly on the plot without a clear visual mapping to the axis ticks, making it difficult to verify the values against the scale.
- **[science]** Figure 7: The x-axis extends to 1000+ decisions, but the caption states the AgenticSTS runs make '~100 strategic calls' and the x-extent is 'not comparable'. Plotting the bounded contract (dashed line) on the same x-axis as the unbounded competitors implies a direct comparison of growth over the same run length, which the caption explicitly denies, creating a misleading visual comparison.
- **[writing]** Figure 7: The legend entry 'AgenticSTS bounded contract (~5k/call, est.)' is ambiguous regarding the y-axis unit. The caption clarifies this is 'strategic user-message median' excluding the 'constant cached system prefix', but the y-axis label is 'Prompt tokens per LLM call'. This discrepancy (partial vs. full prompt) is not visually distinguished in the legend or axis, potentially confusing the reader about what is being measured.
- **[writing]** Figure 8: The legend labels 'AgenticSTS (full-frozen)' and 'AgenticSTS (baseline-strict)' are not defined in the figure caption, which only refers to them generically as 'our cells'.
- **[science]** Figure 8: The x-axis label 'Fresh LLM tokens per run' is ambiguous because the legend explicitly states that the diamond markers (AgenticSTS) use 'estimated' tokens based on a convention, whereas the competitor markers use 'measured' tokens; the axis label should reflect this mixed data source.
- **[science]** Figure 9: The caption claims the figure shows 'combat planning (left) and shop planning (right)', but the rendered image is a single screenshot of a combat encounter with no right-side panel or shop interface visible.
- **[science]** Figure 9: The image displays a game UI (Slay the Spire) rather than the 'decision states used in the prompt' (e.g., text logs or structured data) described in the caption.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 4.1, Eq. 1: The symbol `π` is used as the composition operator without definition. While `π` is standard for policies, here it denotes a prompt assembly function. Define it explicitly: 'where π is the prompt composition function that concatenates...'
- **[writing]** Section 4.2: The terms 'operator prompts' (L1), 'state-typed prompts' (L2), and 'game knowledge' (L3) are introduced as proper nouns for specific layers. While the context implies their function, a brief parenthetical gloss at first use (e.g., 'L1 operator prompts (immutable role templates)') would aid an adjacent-field reader.
- **[writing]** Section 4.3: The routing tiers 'fast', 'strategic', 'analysis', and 'evolution' are used as specific technical categories. Define the criteria for each tier (e.g., 'fast: trivial combat plans; strategic: ordinary decisions') in the first sentence of the paragraph to clarify the distinction for non-specialists.
- **[writing]** Section 5.1: The condition names 'mode-a', 'mode-b-frozen', and 'full-frozen' are used as specific experimental labels. While defined in the text, they appear as code-like identifiers. Ensure the first mention of each includes a brief operational description (e.g., 'mode-a (human-authored L5 seed bodies)') to prevent confusion with generic modes.
- **[writing]** Section 7: The term 'MCP' is used in 'STS2MCP' and 'MCP server' without expansion. While likely 'Model Context Protocol' in this ecosystem, it is not a universal standard. Define the acronym at first use in Section 7 or the Introduction.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically sound and internally consistent. The central thesis—that a bounded, typed memory contract enables ablation and inspection of long-horizon agent decisions—is supported by a coherent chain of premises and conclusions.

1.  **Premise-Conclusion Alignment:** The introduction establishes the problem (unbounded context growth obscures causal attribution) and proposes the solution (typed retrieval). The results section (Section 6) directly addresses this by presenting a fixed-$A_0$ ablation matrix where the "no-scaffold" baseline is compared against configurations with specific layers ($L_4$, $L_5$) enabled. The conclusion that $L_5$ (skills) drives the largest observed lift ($3/10 \to 6/10$) follows directly from the data in Table 1, and the authors correctly qualify this as "directional" rather than statistically significant ($p \approx 0.37$), avoiding the non-sequitur of claiming definitive causality from a small sample.

2.  **Consistency of Definitions and Numbers:** The five-layer architecture ($L_1$–$L_5$) is defined in Section 4 and used consistently throughout the methodology (Section 5) and results (Section 6). The sample sizes are consistent: the headline fixed-$A_0$ analysis uses a balanced subset of 50 games ($5 \times 10$), while the total archive contains 298 trajectories. The text explicitly distinguishes between the headline ablation and the diagnostic streams (cross-backbone, ladder), preventing scope inflation. The derived score formula (Eq. 1) is applied consistently in the text and the appendix tables.

3.  **Handling of Limitations:** The paper avoids internal contradiction by explicitly stating in the Limitations (Section 10) and Conclusion (Section 9) that the comparison to accumulating-context agents is "operational" rather than a controlled ablation. This aligns with the methodology, which notes that a matched same-codebase accumulating-context cell is future work. The claim that the bounded contract "outperforms" competitors is carefully framed as an observation of the current state of practice (Section 7) rather than a proven causal superiority of the contract itself, which is logically consistent with the lack of a controlled baseline.

4.  **No Circular Reasoning:** The argument does not assume the conclusion. The effectiveness of the $L_5$ layer is an empirical finding derived from the ablation, not a premise used to justify the architecture. The "bounded" nature of the contract is a design choice, and its benefits (inspectability, ablation) are demonstrated, not assumed.

The reasoning holds together: the premises (design of the testbed, ablation results) support the conclusions (typed retrieval isolates variables, $L_5$ is the primary driver of performance in this setup) without logical gaps or contradictions.

## paper_reviewer_overreach — verdict: accept

The paper demonstrates exceptional discipline in aligning its rhetorical scope with the actual evidentiary boundaries of its experiments. Unlike many works in the agentic systems space that extrapolate single-benchmark wins to universal solutions, this manuscript consistently frames its contributions as specific to the "bounded-memory contract" within the *Slay the Spire 2* testbed.

The abstract explicitly qualifies the headline result ($3/10$ vs $6/10$ wins) as "directional rather than statistically decisive" ($p \approx 0.37$), preventing the common overreach of presenting a small-sample trend as a definitive breakthrough. Similarly, the introduction and results sections carefully distinguish between "operational comparisons" (e.g., against STS2MCP and CharTyr) and "controlled tests," acknowledging that differences in game patches and routing prevent a clean causal attribution of the performance gap solely to the memory contract.

The "Limitations" section is robust and substantive, directly addressing the most significant scope boundaries: the lack of a same-codebase accumulating-context baseline, the restriction to a single character (Silent), and the training-free nature of the evaluation. The conclusion mirrors the body's caution, stating that whether a bounded contract "outperforms a matched accumulating-context design remains an open question," rather than asserting it as a proven fact.

There are no instances of "solves," "proves," or "universally" language that exceed the data. The paper successfully avoids the trap of presenting a novel testbed as a solved problem, instead positioning it as a reusable methodology for future inquiry. The scope of the claims is tightly bound to the 298 trajectories and the specific ablation matrix presented.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a low-risk research artifact: a bounded-memory testbed for LLM agents operating within a single-player video game environment (Slay the Spire 2). The work does not involve human subjects, personal data, or sensitive real-world interactions.

The "Ethical Considerations" section (sec/11.ethics.tex) is present and appropriately scoped. It correctly identifies that no human subjects are involved, no personal data is collected, and the game/mod licensing is respected (using local regeneration of game strings rather than redistributing copyrighted assets). The authors explicitly address the "Risk of dual use," noting that while the underlying agent capabilities are general, the current deployment is confined to a game setting with low direct harm, and they acknowledge that deployment in real-world domains would require separate safety reviews.

There are no indications of:
- Dual-use capabilities described without mitigation (the method is a memory interface for a game agent).
- Human-subjects data without consent (none used).
- PII or re-identifiable data exposure (trajectories are game states).
- Scraped data used against license terms (the paper explicitly avoids redistributing game assets and cites community mods with appropriate provenance).
- Systems designed to deceive or surveil (the agent plays a game).
- Operational details for biohazard or cyber-offense (none present).

The paper is a standard methodological contribution in the AI agent space with appropriate, albeit brief, ethical disclosures suitable for the low-risk nature of the work. No action items are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a novel testbed for bounded-memory agents and is remarkably transparent about the statistical limitations of its primary results. The authors correctly identify that the headline win-rate improvement (3/10 to 6/10) is "directional rather than statistically decisive" (p≈0.37). However, the evidentiary strength of the paper relies heavily on interpreting these directional trends and operational comparisons as support for the "bounded contract" hypothesis. The primary concern is

## paper_reviewer_statistical_analysis — verdict: accept

The statistical treatment in this paper is exemplary for the field of LLM agent evaluation, particularly given the small sample sizes inherent to long-horizon game runs. The authors correctly identify that their primary headline result (3/10 vs 6/10 wins) is underpowered for a definitive significance claim and explicitly label it "directional" rather than "statistically significant."

Specifically, the choice of the Fisher exact test for the $2 \times 2$ contingency table (Section 6.2) is the correct parametric-free approach for small counts ($N=10$ per cell), and the reported $p \approx 0.37$ is consistent with the observed data. The use of Wilson score intervals for win rates (Section 5.3, Appendix) is appropriate for binomial proportions, especially where $p$ is near 0 or 1 or $n$ is small, avoiding the under-coverage issues of the standard Wald interval. The bootstrap method (5,000 resamples) for continuous score distributions is also a robust choice given the non-normal nature of game scores.

Crucially, the authors avoid the common pitfall of "p-hacking" or over-interpreting non-significant trends. They do not claim the $L_5$ skill layer is "significantly better" despite the point estimate lift; instead, they transparently report the overlap in confidence intervals and the high p-value. The separation of the fixed-$A_0$ ablation (balanced $N=50$) from the diagnostic cross-backbone and ladder streams prevents inappropriate pooling of heterogeneous data. The reporting of exact denominators (e.g., "0/5" for cross-backbone wins) and the explicit distinction between "operational comparisons" and "controlled tests" further ensures that the numbers mean exactly what the text claims. No statistical errors, missing uncertainty measures, or misapplied tests were found.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the core argument regarding bounded memory contracts is presented with logical progression. However, several instances of dense phrasing and abrupt transitions impede the reader's momentum, requiring re-reading to parse the intent. In the Abstract, the final sentence is overloaded with a complex noun phrase ("an agent design and a validated, reusable methodology...") that serves as the conclusion. This creates a "garden-path" effect where the reader mus
