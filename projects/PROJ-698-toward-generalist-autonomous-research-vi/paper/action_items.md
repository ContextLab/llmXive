# Automated-review action items — Toward Generalist Autonomous Research via Hypothesis-Tree Refinement

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Abstract and Sec 3.2 cite 'GPT-5.5' and 'Claude Opus 4.6' as baselines. These models are not publicly documented as of 2026. Verify their existence or replace with public baselines to support the SOTA claim.
- **[writing]** Sec 3.2 cites 'terminalbench' (arXiv:2601.11868) for 'Terminal-Bench 2.0' (36 dev/53 test). Confirm the cited paper explicitly defines this specific version and split, or update the citation.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption contains a placeholder artifact name ('Agent-level implementation details of .') instead of the actual system name, rendering the description incomplete.
- **[science]** Figure 1: The 'Verified Merge Gate' section depicts a workflow where a branch is 'rejected' and 'retained as evidence' (red box), but the diagram does not show the data flow or feedback loop for how this evidence is returned to the 'Persistent Coordinator Agent' to update the hypothesis tree.
- **[writing]** Figure 2 caption is incomplete: the title 'Toward Generalist Autonomous Research via Hypothesis-Tree Refinement' is missing from the start of the caption text.
- **[science]** Figure 2b: the 'Claude Code 8.33' and 'Code/6.75' annotations are placed near the end of the timeline but lack clear visual markers (e.g., dots or lines) connecting them to specific points on the graph, making it ambiguous which cycle they refer to.
- **[writing]** Figure 2c: the y-axis label 'Model Training' is not clearly associated with the grouped bars; a clearer grouping label or spacing would improve readability.
- **[fatal]** Figure 3: The rendered image is extremely low-resolution and illegible; text labels, node content, and specific connection lines are unreadable, making it impossible to verify the framework described in the caption.
- **[science]** Figure 3: The diagram contains a large number of distinct icons and colored nodes (e.g., in the sidebars and central tree) but lacks a visible legend or key to define their meanings.
- **[writing]** Figure 4: The legend in panel (a) uses the name 'Gemini 3 Flash', but the caption refers to the system generically as 'is rerun' without naming the specific models used, creating a disconnect between the visual data and the textual description.
- **[writing]** Figure 4: Panel (b) legend uses 'Init' and 'After run', but the caption describes the experiment as evaluating a 'frozen' harness; the term 'After run' is ambiguous and does not clearly map to the 'frozen' state described in the text.
- **[science]** Figure 5: The y-axis uses a non-standard, broken logarithmic scale (0, 2, 5, 10, 50, 100, 250, 500, 1000, 2000) where the distance between 0 and 2 is visually similar to 2 and 5, making the data points near zero misleadingly spread out and the scale difficult to interpret.
- **[writing]** Figure 5: The caption contains a blank space where a model name should be ('for , the total further sums...'), likely referring to the system (Arbor) but failing to explicitly name it.
- **[fatal]** Figure 6: The caption references 'Table .' (missing number) for the annotated test scores, making the data unverified.
- **[science]** Figure 6: The y-axis label 'per-node dev gain (% of Arbor's final dev gain)' contradicts the caption's claim that the curves show 'best-so-far development gain'; the label implies a normalization that is not explicitly described in the text.
- **[writing]** Figure 6: The legend uses symbols (circle, star) that are not defined in the legend box itself; the reader must rely on the caption to understand that circles represent 'admitted node' and stars represent 'held-out test best'.
- **[writing]** Figure 7: The text 'purned' appears under nodes N1.1, N2.1, N5.1, and N6.2; this is likely a typo for 'purnished' or 'burned' and should be corrected for clarity.
- **[writing]** Figure 7: The text 'dianPersona diversity' in the 'Evidence Sharing' box appears to be a typo (likely 'diverse Persona' or similar) and is unclear.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3 (Task Formulation) introduces the symbol $\Mat$ (e.g., $\Mat_0$, $\Mat^\star$) without definition. A competent reader from an adjacent field cannot infer if this denotes a matrix, a material, or a generic artifact. Define $\Mat$ as 'the mutable artifact (e.g., codebase, model weights)' at first use.
- **[writing]** Section 3 defines $\Eval_{\dev}$ and $\Eval_{	est}$ but does not explicitly state that $\Eval_{\dev}$ is used for search guidance while $\Eval_{	est}$ is held-out for final validation. While implied by the subscripts, a one-sentence gloss (e.g., 'where $\Eval_{\dev}$ guides exploration and $\Eval_{	est}$ is held-out') would prevent confusion for non-specialists.
- **[writing]** Algorithm 1 (Section 4.2) uses the notation $	extsf{path}(n_0	o n)$ and $	extsf{ch}(a)$ without defining them in the algorithm caption or surrounding text. Define these as 'the path from root to node n' and 'the set of children of node a' respectively.
- **[writing]** Section 4.1 introduces the term 'worktree' (e.g., 'isolated worktrees') assuming familiarity with Git's worktree feature. Add a brief parenthetical gloss (e.g., 'isolated Git worktrees (separate working directories)') to ensure readers from non-systems backgrounds understand the isolation mechanism.
- **[writing]** Section 5.1 mentions 'Muon' baseline without a brief descriptor. While 'Muon' is a specific optimizer, a short gloss (e.g., 'Muon, a second-order optimizer') would help readers from adjacent fields (e.g., NLP or RL) who may not know this specific ML engineering tool.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Transfer Logic (Section 5.2): The claim that a harness optimized on BrowseComp "transfers" to HLE and DeepSearchQA implies a causal link between the specific optimizations found in BrowseComp and the gains in the other tasks. The text reports the final scores (25.50% $\to$ 31.50%) but does not explicitly state that the *same* optimized artifact or specific strategy was applied to the transfer tasks, nor does it define the baseline for these transfer metrics. Without clarifying that the exact art

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title 'Toward Generalist Autonomous Research' and abstract claim 'best held-out result on six real tasks' imply broad generalism. Experiments (Sec 5) cover only 6 engineering/data tasks. Limitations (App A) admit untested domains like biology/physics. Replace 'Generalist' with 'Engineering-focused' or qualify the abstract to 'across the six evaluated tasks'.
- **[writing]** Section 5.5 claims transfer to HLE/DeepSearchQA 'proving discovery of generalizable design changes'. Evidence is limited to two search benchmarks. Change 'proving' to 'suggesting potential for' and acknowledge the narrow scope of the transfer test.
- **[writing]** Conclusion states 'Persistent hypothesis management is a key abstraction for autonomous research' universally. Limitations (App A) note failures in deep domain knowledge outside tested tasks. Hedge to 'for the class of optimization tasks tested' to match evidence scope.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a framework for autonomous research agents (Arbor) operating on software engineering and data synthesis benchmarks. The work does not involve human subjects, personal data, or sensitive biological/chemical domains, and thus raises no immediate consent or privacy concerns.

The primary safety consideration is the dual-use potential of an autonomous system capable of optimizing codebases and generating data pipelines. However, the paper explicitly restricts the evaluation to benign, controlled environments (e.g., NanoGPT-Bench, BrowseComp, MLE-Bench Lite) and employs a "held-out merge gate" to prevent overfitting to development metrics. The system is not described as having capabilities to autonomously discover and exploit zero-day vulnerabilities in live systems, nor does it generate deceptive content or malware. The "Data Synthesis" tasks involve generating math problems and search queries, which are standard research artifacts.

The authors acknowledge limitations regarding the scope of evaluation and the potential for agents to reverse-engineer solutions from scores (Appendix, Limitations), which serves as an adequate disclosure of the system's current constraints. There is no evidence of operational details that would facilitate immediate harm (e.g., specific exploit payloads or instructions for bypassing safety filters). Consequently, the paper does not present a foreseeable, non-trivial risk of harm that is unaddressed. The research falls within the standard norms of autonomous agent benchmarking.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling framework (Arbor) for autonomous research, but the evidentiary support for the magnitude of the reported gains relies on experimental designs that do not fully rule out alternative explanations such as luck, baseline asymmetry, or confounded starting conditions. First, the stability of the reported improvements is unclear. Table 2 (Main Results) reports specific held-out scores (e.g., 3237.5 steps for Optimizer Design) and claims they are averages of two seeds. Ho

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Table 2 report 'test averages two seeds' for Model Training tasks but provide no standard deviation, standard error, or confidence intervals. Report mean ± SD or 95% CI for all metrics, or explicitly state that only two seeds were run and the variance is too high to support precise claims.
- **[writing]** Table 2 reports performance to two decimal places (e.g., 77.36%) for tasks with small test sets (e.g., 53 tasks). A single task success represents ~1.89%, making the second decimal place statistically meaningless. Round all percentage metrics to one decimal place or the nearest integer consistent with the denominator size.
- **[writing]** Section 4.3 and Table 2 claim Arbor is 'best' across multiple baselines without reporting p-values, effect sizes, or multiple-comparison correction. If formal testing was performed, report the test and apply a correction (e.g., Holm-Bonferroni). If not, rephrase claims to 'higher mean performance' and report variance across seeds.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the prose is clear, allowing the reader to follow the argument from the problem formulation to the results. The use of bolding for key requirements in Section 4.1 and the clear separation of the Coordinator and Executor roles in Section 4.2 are effective. However, there are a few specific instances where the flow is interrupted by structural redundancies or missing signposts. First, Section 3 contains a duplicate \label command (\label{sec:task}\label{s
