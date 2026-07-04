# Automated-review action items — Scaling the Horizon, Not the Parameters: Reaching Trillion-Parameter Performance with a 35B Agent

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several strong comparative claims against "1T-parameter models" and specific baselines that require verification. The abstract and introduction assert that Agents-A1 outperforms Kimi-K2.6 and DeepSeek-V4-pro on a list of benchmarks. While Table 1 supports the claim for SEAL-0, the text generalizes this to "outperforms 1T models" without acknowledging that the model loses to GPT-5.5 (another 1T+ class model) on BrowseComp and XBench-DS. This is a minor overstatement of the results

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption 'Benchmark performance of [Fig1_a1_benchmarks_altair_grid-8.pdf]' is a filename placeholder rather than a descriptive summary of the data shown.
- **[writing]** Figure 1: The legend at the top uses icons that are not explicitly defined in the caption, requiring the user to infer the mapping between the icons and the model names (e.g., 'Agents-A1', 'Qwen3.6-35B-A3B').
- **[writing]** Figure 2: The caption contains a grammatical error ('Optimization trajectory of on the...') and includes a raw filename ('[appendix_mle.png]') that should be removed.
- **[science]** Figure 2: The x-axis label 'Time (hours)' is ambiguous; the caption mentions 'wall-clock time' but does not specify if this is elapsed time or cumulative compute time, which is critical for interpreting the '12-hour run' claim.
- **[writing]** Figure 3: The caption text is truncated at the end ('with tria [appendix_earth.png]'), cutting off the description for panel (d).
- **[science]** Figure 3: Panel (e) y-axis labels use cardinal directions (N, S, E, W) alongside degrees (0°, 90°, etc.), which is non-standard and potentially confusing for a heading scale (0-360°).
- **[writing]** Figure 3: Panel (d) legend includes 'Speed increase' and 'Speed decrease' markers, but the caption does not describe these specific annotations.
- **[science]** Figure 4: The diagram shows a loss function formula at the bottom, but the caption does not explain what the formula represents or how it relates to the 'salient vocabulary alignment' mentioned.
- **[writing]** Figure 4: The title 'Multi-domain Data' lists 'Search', 'Science', 'Engineering', 'Agent Tasks', and 'Inst. Following', but the diagram's query boxes only show 'Search data', 'Science data', 'Engineering data', and 'Inst. data' — 'Agent Tasks' is missing from the query section.
- **[science]** Figure 4: The flow from 'Queries of ... data' boxes to the loss function lacks clear arrows or labels indicating how these queries feed into the training process described in the caption.
- **[writing]** Figure 5: The caption contains a grammatical error ('infrastructure of .') where the model name is missing.
- **[writing]** Figure 5: The 'Training corpus' section lists 'Data base' with a space, which is non-standard terminology compared to 'Database'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 2.1 (Eq. 1) introduces the symbol $\mathcal{B}_d$ in the phrase 'Given a domain $\mathcal{B}_d$' without defining it. The subsequent definition of $\mathcal{G}_d$ uses $\mathcal{C}_d, \mathcal{A}_d, \mathcal{O}_d, \mathcal{V}_d$ but never explicitly states what $\mathcal{B}_d$ represents (e.g., 'the set of tasks in domain d' or 'the domain label'). Define $\mathcal{B}_d$ at first use.
- **[writing]** Section 2.2 (Eq. 2) introduces the symbol $ot$ in the trajectory definition ($v_t \in \mathcal{V}_q \cup \{ot\}$) without a textual explanation. While common in logic, in this context it is unclear if it means 'no verifier fired', 'verification failed', or 'undefined'. Add a brief clause: 'where $ot$ denotes the absence of a triggered verifier'.
- **[writing]** Section 2.3 introduces 'SVA' (Salient Vocabulary Alignment) and 'OPD' (On-Policy Distillation) as acronyms. While 'OPD' is defined in the section title, 'SVA' is only introduced as a phrase in the text without the acronym expansion in parentheses at first use (e.g., 'salient vocabulary alignment (SVA)'). Ensure both are explicitly expanded at first occurrence in the body text.
- **[writing]** Section 3.1 (Eq. 10) uses the symbol $\lambda_{\mathrm{neg}}$ in the advantage equation without defining its value or role in the text preceding the equation. The text mentions 'asymmetric design' but does not explicitly state that $\lambda_{\mathrm{neg}}$ is a weighting coefficient for the process reward on negative samples. Define $\lambda_{\mathrm{neg}}$ where it first appears.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Section 4.2.1 claims GAIA score increases to 85.4, but Table 5 (search_rl.tex) shows 95.1. Correct the text to match the table value (95.1) or verify the table data.
- **[writing]** Section 4.2.1 states the search-enhanced teacher improves HLE from 47.4 to 50.3. Table 5 confirms this, but Table 6 (Science-enhanced) also lists 47.4 as baseline. Explicitly clarify in text that 47.4 is the shared baseline for all teachers to avoid confusion about which teacher achieved 50.3.
- **[writing]** Section 4.2.2 references 'Table 8' for OPD results, but the main results table is labeled `tab:main_results` (likely Table 4). Update text to reference the correct table label or ensure final PDF numbering matches the text's 'Table 8' claim.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title and Abstract claim 'Reaching Trillion-Parameter Performance' and 'match the performance of 1T models.' Table 1 shows the model is outperformed by 1T models (GPT-5.5, Kimi-K2.6) on 6 of 14 benchmarks (e.g., MLE-Bench-Lite: 43.9 vs 72.7; SciCode: 44.3 vs 56.1). Replace 'match' with 'compete with on specific long-horizon benchmarks' and qualify the title to reflect performance parity only on a subset of tasks, not a general equivalence.
- **[writing]** Abstract states the method 'reaches trillion-parameter-level performance' based on results from a single 35B model family (Qwen3.5 derivatives). The conclusion implies this scaling path is a general solution for 'any' agent. Add a limitation explicitly stating that the 'trillion-parameter' claim is specific to the tested benchmarks and model architecture, and that generalization to other domains or model families remains untested.
- **[writing]** The Introduction and Abstract frame the work as a 'practical path' to replace parameter scaling. However, the results show the method fails to close the gap on engineering tasks (MLE-Bench) where parameter scaling clearly wins. The narrative omits this failure mode. Add a sentence in the Limitations section acknowledging that for tasks requiring deep internal knowledge or complex engineering workflows, parameter scaling still outperforms horizon scaling in the current regime.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a 35B Mixture-of-Experts agent model trained on long-horizon trajectories across six domains (search, engineering, science, instruction following, tool calling, and general agentic tasks). From a safety and ethics perspective, the work does not exhibit foreseeable, non-trivial risks that are unaddressed.

The data pipeline described in Section 3 (data_pipeline.tex) relies on public benchmarks (e.g., MLE-Dojo, Kaggle competitions, WildChat-1M, NVIDIA Nemotron-RL) and synthetic data generation via self-play and tool-augmented search. The paper explicitly states that trajectories are collected in sandboxed environments or from public sources, and no Personally Identifiable Information (PII) or sensitive human-subjects data (e.g., medical records, private communications) is released or used without consent. The use of "simulated users" in tool-calling tasks (Section 3.5) is a standard synthetic data technique and does not constitute covert surveillance or deception of real individuals.

The model's capabilities (long-horizon planning, tool use, code generation) are dual-use by nature, as is common in the field of agentic AI. However, the paper does not describe a novel method that specifically lowers the barrier to a concrete harmful act (e.g., automated vulnerability exploitation, biological synthesis, or targeted disinformation generation) beyond the general capabilities of existing frontier models. The evaluation benchmarks (e.g., GAIA, HLE, SciCode) are standard academic tests for reasoning and tool use, not operational attack simulations. The authors do not release operational exploit code or actionable attack recipes; the "12-hour optimization run" (Section 5.3.1) is a benign machine learning engineering task.

There are no missing disclosures regarding human subjects, IRB approval, or data licensing violations. The paper acknowledges limitations in Section 6 but does not require a specific safety addendum for the risks identified, as the risks are inherent to the class of models being studied and are not exacerbated by specific, unmitigated methodological choices in this work. The verdict is `accept` with no action items required for this lens.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling narrative for scaling agent horizons, but the experimental design in Section 4 and Tables 1-3 contains critical gaps that prevent the evidence from fully supporting the headline claims of "trillion-parameter performance" and specific mechanism attribution. First, the stability of the reported results is unverified. Table 1 presents single-point accuracy scores (e.g., 56.4 on SEAL-0, 80.6 on IFBench) without any measure of variance. For benchmarks with small test s

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical reporting in this paper is generally consistent with common practices in large-scale LLM benchmarking (reporting point estimates), but it lacks the necessary uncertainty quantification to support the strong comparative claims made in the text. Specifically, Section 4.1 mentions that MLE-Bench-Lite results are averaged over three seeds, yet Table 1 and Table 3 present only single point estimates (e.g., 43.9) without standard deviations, standard errors, or confidence intervals. In

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and readable, with a clear narrative flow from the problem statement to the proposed solution and results. However, there are several instances of grammatical errors, sentence fragments, and weak transitions that disrupt the reader's momentum, particularly in the Experimental Results section. In Section 3.1, the explanation for the performance drop in full-domain SFT is presented as two disjointed sentences, the second of which lacks a clear connection to t
