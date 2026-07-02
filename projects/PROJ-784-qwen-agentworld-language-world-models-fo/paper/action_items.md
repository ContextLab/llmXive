# Automated-review action items — Qwen-AgentWorld: Language World Models for General Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 5 claims an +8.66 gain at 35B scale, but Table 1 omits the 35B baseline. Clarify the reference model for this gain.
- **[writing]** Section 6 states concurrent work 'doubles performance' without specifying the baseline metric. Define the baseline for this claim.
- **[writing]** Section 7 compares Sim RL (50.3%) to Real RL (45.6%) but does not specify if the baseline is the 35B or 397B model. Clarify the comparison.
- **[writing]** Section 4 cites consistency rho=0.92-0.99 without breaking down by dimension. Specify which dimensions correspond to these bounds.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains raw LaTeX formatting artifacts (e.g., '=1.5ptcolordecoupleDecouple') and missing model names (e.g., 'Overview of .') instead of clean text.
- **[science]** Figure 1: The top bar chart legend lists 'Qwen-AgentWorld-397B-A17B' as the purple bar, but the x-axis label for that bar is simply 'Ours', creating a disconnect between the legend and the axis.
- **[writing]** Figure 1: The bottom-left section contains a text label 'Generalize to Claw Agent' that appears to be a caption fragment or typo rather than a clear description of the data.
- **[writing]** Figure 2: The caption refers to '-397B-A17B' (likely a placeholder or typo for the model name), which is not defined in the caption or other provided text.
- **[writing]** Figure 3: The 'Terminal' panel contains a rendering artifact where the text 't(1)e(2)s(3)...x(24)t(25)/n(26) -> 26 bytes' is displayed as a single unbroken line, making the character enumeration and byte count calculation difficult to read.
- **[writing]** Figure 3: The 'MCP' panel text 'UUID fomat' contains a spelling error (should be 'format').
- **[science]** Figure 6: The legend defines 'Real RL' and 'Sim RL', but the caption fails to define these terms or explain the experimental comparison (e.g., training on real vs. simulated data), making the figure's scientific claim unintelligible without external context.
- **[writing]** Figure 6: The y-axis label 'Score (%)' is ambiguous; it is unclear if the values (e.g., 50) represent a percentage (0-100) or a raw score scaled to 100, which affects the interpretation of the F1 metric.
- **[writing]** Figure 7: The 'Source benchmarks' legend uses color swatches to map to domains, but the text labels (e.g., 'MCP Mark 6', 'Wide Search') are too small and low-contrast to be legible.
- **[writing]** Figure 7: The 'Avg. context length' and 'Avg. trajectory turns' charts use color-coding for domains (e.g., red for Web/Android), but the specific color-to-domain mapping is not explicitly defined in a legend, relying on the viewer to infer it from the 'Source benchmarks' section.
- **[science]** Figure 8: The caption claims to show 'five-dimensional rubric mean per domain,' but the chart displays a single score per model per domain (likely an aggregate) without showing the five dimensions or their breakdown.
- **[writing]** Figure 8: The y-axis label 'Text-based' and 'GUI' is positioned on the far left, but the chart contains seven subplots (Terminal, MCP, Search, SWE, Android, Web, OS) where only the first two are text-based and the last three are GUI; the labels do not clearly demarcate the grouping of the middle subplots.
- **[writing]** Figure 8: The x-axis labels for models are cramped and multi-line (e.g., 'Claude Opus 4.8'), making them difficult to read; consider rotating or simplifying.
- **[science]** Figure 9: The legend lists 'Terminal' (red circles), but the caption states the model was trained on Terminal data alone. If Terminal is the training domain, it should not be plotted as a held-out transfer result in panel (b) alongside MCP, SWE, and Search; the inclusion of the training domain in the transfer plot is conceptually confusing or mislabeled.
- **[writing]** Figure 9: The y-axis label 'Score (0-100)' is present, but the specific metric (e.g., F1, Accuracy, Pass@1) is not defined in the caption or axis label, making the absolute values ambiguous.
- **[writing]** Figure 10: The caption begins with a missing subject (e.g., 'Qwen-AgentWorld' or 'The model'), reading as 'unifies seven categories...' instead of a complete sentence.
- **[writing]** Figure 10: The caption text 'unifies seven categories' does not match the visual content, which depicts eight distinct categories (MCP Servers, Search Engine, IDE, Terminal/CLI, Android System, Web Browser, Operating System, and a central hub).
- **[writing]** Figure 12: The caption contains a grammatical error ('Three-stage training pipeline of .') where the model name is missing after the preposition 'of'.
- **[writing]** Figure 12: The top-level title 'CPT injects, SFT activates, RL sharpens' is not explicitly defined in the caption, which uses slightly different verbs ('instills', 'sharpens') for the same stages.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Expand every acronym (CPT, SFT, RL, LWM, GSPO, MCP, Sim RL, Real RL) to its full form at the very first occurrence in the text.
- **[writing]** Consider replacing "Sim RL" and "Real RL" with "Simulation-based RL" and "Real-environment RL" in the first instance to reduce cognitive load.
- **[writing]** Ensure that "MCP" is defined as "Model Context Protocol" (or the specific full name intended) in the Introduction or the domain taxonomy table. These changes are purely editorial and would not alter the scientific content but would make the paper significantly more readable for a broader audience.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent logical framework for training Language World Models (LWMs) via a three-stage pipeline (CPT, SFT, RL) and demonstrates their utility in simulation and as agent foundations. The causal chain from "next-state prediction" to "improved agent performance" is well-supported by the experimental results in Table 4, where the LWM RL warm-up leads to consistent gains across diverse benchmarks. The internal logic of the "Decoupling" vs. "Unifying" paradigms is sound, and the d

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that Sim RL 'surpasses' Real RL (Section 5.1.2) is overreaching. The data shows Sim RL (50.3%) outperforms Real RL (45.6%) on WideSearch F1 Item, but the paper generalizes this to a broad superiority of simulation without addressing domain specificity or the potential for overfitting to the simulated environment's quirks.
- **[science]** The assertion of 'Radical cross-task generalization' (Section 5.2) overstates the evidence. While gains are reported on 7 benchmarks, the transfer is from single-turn non-agentic LWM RL to multi-turn agentic tasks. The paper does not sufficiently discuss the limitations of this transfer or the specific conditions under which it might fail, implying a universality not fully supported by the data.
- **[writing]** The claim that the model achieves 'perfect consistency' in MCP schema reproduction (Section 4.2) is likely an overstatement. The text states 'perfect consistency' across nine calls, but without explicit statistical evidence or a definition of 'perfect' in this context (e.g., 100% match on all fields), this phrasing risks exaggerating the model's reliability.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes training agents on 'fictional-world construction' (e.g., 2030 Mars migration) and 'controllable simulation' of errors. Explicitly address the dual-use risk of these capabilities being used to generate highly realistic disinformation, deepfakes, or social engineering scenarios. A dedicated 'Safety and Limitations' subsection is required.
- **[writing]** The evaluation relies heavily on LLM judges (e.g., GPT-5.2) to score 'Realism' and 'Factuality' of simulated environments. Discuss the risk of reward hacking or 'self-praise' (noted in Section e002) leading to over-optimistic safety assessments where the model learns to mimic safety signals without genuine alignment.
- **[writing]** The benchmark includes 'SWE' (Software Engineering) and 'Terminal' domains where the model predicts execution outputs. Clarify if the training data or evaluation includes potentially harmful code (e.g., malware, exploits) and confirm that the 'Rule-Based Verifier' includes safety filters to prevent the generation of dangerous payloads during the simulation phase.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that Sim RL (50.3%) outperforms Real RL (45.6%) on WideSearch (Table 3, Fig 4) lacks statistical validation. With only two data points per condition (35B and 397B models), the difference could be noise. Report confidence intervals or p-values from multiple seeds to rule out random variance.
- **[science]** The 'Rule-Based Verification' results (Table 4) show GPT-5.4 outperforming the proposed method on average (72.93% vs 67.12%), yet the text claims the proposed method 'surpasses frontier models on GUI domains' without specifying which specific GUI metrics or domains justify this generalization. Clarify the scope of this claim or adjust the wording.
- **[science]** The analysis of 'Deliberative Self-Correction' cites 1,347 interrupts across 129 turns (approx. 10.4/turn). This sample size (n=129) is small for drawing broad conclusions about reasoning patterns across four distinct domains. Provide the distribution of turns per domain and confirm if the 'Wait!' pattern is statistically significant across all domains or driven by a single one (e.g., SWE).

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 3 (Experiments) and Table 1 report point estimates (e.g., 58.71 vs 58.25) without confidence intervals, standard errors, or p-values. Given the high variance in LLM benchmarks, statistical significance testing (e.g., bootstrap or t-tests) is required to validate the claimed superiority over GPT-5.4.
- **[science]** Section 4 (Terminal-Bench 2.0) and Table 3 show improvements (e.g., +8.96 average) but lack multiple-comparisons correction. With 14 baselines and 7 domains tested, the risk of Type I error is high. Apply Bonferroni or FDR correction to reported significance claims.
- **[science]** Section 5 (Analysis) cites '129 thinking traces' and '1,347 interrupts' as evidence of reasoning patterns. The sampling strategy for these traces is not described (random vs. cherry-picked). A statistical power analysis or randomization protocol is needed to ensure these qualitative patterns are representative.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Preliminaries), the definition of the unified schema uses the symbol \oplus without prior definition or context. Define this operator or replace with standard concatenation notation to ensure clarity for readers unfamiliar with the specific formalism.
- **[writing]** Section 5 (Experiments) and Section 6 (Terminal-Bench 2.0) contain inconsistent capitalization and spacing in benchmark names (e.g., 'SWE-B V' vs 'SWE-Bench Verified', 'Claw' vs 'Claw-Eval'). Standardize these names to match the full titles used in the Introduction and Table 1 for consistency.
- **[writing]** The phrase 'CPT injects, SFT activates, RL sharpens' in the Introduction is a catchy slogan but lacks immediate grammatical parallelism with the surrounding prose. Consider rephrasing to 'CPT injects knowledge, SFT activates reasoning, and RL sharpens fidelity' or similar to improve flow and clarity.
- **[writing]** In Section 3 (Training Recipe), the sentence 'Reward = 90% Five-Dimensional Rubric (LLM Judge) + 10% Rule-Based Verifier' is slightly ambiguous regarding whether the percentages refer to weight or score contribution. Rephrase to 'The reward signal comprises a weighted sum: 90% from the Five-Dimensional Rubric... and 10% from the Rule-Based Verifier'.
