# Automated-review action items — SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** In Section 3 (Results), the text claims a +11.2 point gain over SpaceTools (Tab. 1). However, Table 1 (action_interface) shows SpaceTools (Structured Tool-Call) averaging 56.7% and SpatialClaw 59.9%, a difference of 3.2 points. The +11.2 figure appears to be the gain over the 'No-tool' baseline (53.4% -> 59.9%) or a different comparison not explicitly defined in the text. This misattribution of the baseline undermines the claim's accuracy.
- **[writing]** Table 1 (action_interface) lists Omni3D results where Structured Tool-Call (55.7) outperforms SpatialClaw (54.3), yet the text in Section 3 states SpatialClaw 'outperforms... across all categories.' This is factually incorrect for the Omni3D benchmark within the Single-image category. The claim requires qualification or correction to reflect that gains are not universal across every single benchmark.
- **[science]** The abstract and introduction claim the framework is 'training-free' and achieves gains 'without any benchmark- or model-specific adaptation.' However, the prompt details (App. Prompts) describe a 'Planner' that maps question shapes to specific tools (e.g., 'coordinates -> vlm.locate + SAM3'). If this mapping logic is hard-coded or requires manual tuning per benchmark type, the claim of 'no adaptation' is overstated. Clarify if the planner is fully zero-shot or relies on pre-defined heuristics.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption begins with a sentence fragment ('wraps a persistent kernel...') lacking a subject; the figure itself labels the system as 'SpatialClaw' (inferred from paper title) or the caption should explicitly name the method.
- **[writing]** Figure 1: The iteration condition at the bottom uses the variable '$N_{max}$' which is not defined in the figure labels; while the caption mentions it, the figure text should ideally define the variable for standalone clarity.
- **[writing]** Figure 2: The caption text is incomplete and grammatically incorrect, missing the method name at the start of sentences (e.g., 'studies code' instead of 'SpatialClaw studies code', 'writes Python' instead of 'SpatialClaw writes Python').
- **[writing]** Figure 2: The caption fails to explicitly define the acronyms 'SAM3' and 'KDTree' used in the code snippets within panels (a) and (c), which may be unclear to readers unfamiliar with the specific libraries.
- **[writing]** Figure 3: The caption contains a grammatical error and missing subject in the first sentence ('Pairwise win/loss margin of over baselines' should be 'margin of SpatialClaw over baselines').
- **[writing]** Figure 3: The caption text 'outperforms both (a) Structured tool-call and (b) Single-pass Code' contradicts the figure labels, where (a) is 'Single-pass Code' and (b) is 'Structured tool-call'.
- **[science]** Figure 3: The x-axis labels for the left panel (a) are inverted relative to the top header; the header indicates 'Single-pass code wins' are to the left, but the axis numbers increase to the left (10, 0, 10, 20, 30), which is non-standard and potentially confusing.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific jargon that creates a barrier for non-specialist readers, particularly in the Introduction and Method sections. First, the term "agentic" is used repeatedly (e.g., "Agentic Spatial Reasoning", "agentic loop") without definition. It is a buzzword in the field but means little to a general reader. The authors should use "autonomous" or "agent-based" and define the concept of an "agent" simply as a system that can make decisions and take actions. Sec

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that 'Removing utility functions (I) yields performance on par with full SpatialClaw' (Sec 5) is contradicted by Table 3. The 'No utility' variant (56.4%) is 0.5% lower than 'Full' (56.9%) and underperforms on 12/20 benchmarks. Clarify that the drop is marginal rather than 'on par' to avoid overstatement.
- **[writing]** Table 1 shows Qwen3.5-397B performance decreases on ERQA (-1.0) and Omni3D (-1.9) with SpatialClaw. However, the abstract claims 'consistent gains across six VLM backbones'. This is a logical contradiction; qualify the claim to 'consistent average gains' or 'gains on most benchmarks'.
- **[science]** The paper claims SpatialClaw is 'training-free' and attributes gains solely to the interface. However, Table 1 shows massive variance in gains across backbones (e.g., +18.6% vs +0.7% on Omni3D). The text must discuss whether the interface benefits smaller models more or if backbone capabilities confound the causal claim, rather than attributing all variance to the interface.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'consistent gains' across all backbones (Abstract) contradicts Table 1 (main_results.tex), where Qwen3.5-397B shows negative deltas on 4/10 single-image benchmarks (e.g., -1.0 on ERQA). Qualify as 'consistent on average'.
- **[writing]** The claim of 'no benchmark-specific adaptation' (Abstract) is contradicted by the 'Planner' role (Sec 3.2, App D) which maps question shapes to tools. Refine to 'without fine-tuning' to avoid over-claiming prompt engineering as zero-shot.
- **[science]** The conclusion over-attributes success to the 'action interface' (Sec 6). Ablation (Table 2) shows removing perception tools drops performance to 51.4% (vs 48.7% No-tool), indicating tools drive most gains, not just the interface. Balance the claim.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Jailbreak the Sandbox: Craft code that bypasses static analysis (e.g., using obfuscation or dynamic attribute access) to access restricted resources.
- **[writing]** Exploit Tool Vulnerabilities: The framework relies on external perception tools (Depth Anything 3, SAM3). If these tools have vulnerabilities, the agent could potentially trigger them to execute arbitrary code or leak memory, effectively bypassing the sandbox. The authors should clarify whether the sandbox is designed to be robust against adversarial agent behavior or if it assumes a benign agent. A brief discussion on the limitations of static analysis in this context is required. Data Privacy
- **[writing]** PII Exposure: The system might inadvertently process or store Personally Identifiable Information (PII) present in the input images.
- **[writing]** Consent: There is no mention of how consent is obtained for data processing, especially if the system is used in public spaces. The authors should add a paragraph in the "Limitations" or "Broader Impact" section addressing data privacy, retention policies, and the necessity of user consent in real-world deployments. Conclusion: While the technical contribution is sound, the safety and ethics discussion is currently superficial. The paper requires a more rigorous treatment of dual-use risks, the

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Report statistical significance (p-values or confidence intervals) for the reported +11.2 point average gain and key benchmark improvements (e.g., DSI-Bench +17.6) to rule out random variance, as only point estimates are currently provided.
- **[science]** Clarify the sample size (N) per benchmark. The text mentions '1,000 samples max' (App. E) but does not confirm if all 20 benchmarks used the full N or if some were subsampled, which affects the validity of the aggregate average.
- **[science]** Provide a variance measure (standard deviation or standard error) for the ablation study results (Tab. 4) to demonstrate that the observed differences between 'Full', 'No utility', and 'No perception' are robust and not due to noise.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or effect sizes) for the reported average accuracy gains (+11.2 points) and per-benchmark improvements. The current text claims consistent gains but lacks formal hypothesis testing to rule out random variance across the 20 benchmarks.
- **[science]** Clarify the multiple-comparisons handling strategy. With 20 benchmarks and 6 backbones, the probability of false positives increases. Explicitly state if corrections (e.g., Bonferroni, Holm-Bonferroni) were applied or if the analysis is treated as exploratory.
- **[science]** Define the unit of analysis for the reported averages. Specify whether the 'Average' metric in Table 1 and Table 2 is a simple arithmetic mean of benchmark accuracies or a weighted mean based on sample counts, and justify the choice given the varying difficulty and size of the 20 benchmarks.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Results), the custom command \paragrapht is used but not defined in the preamble. This will cause a compilation error. Replace with standard \paragraph or define the command.
- **[writing]** In Section 5, the text references 'Tab.~\ref{tab:comparison_agents}', but no such label exists in the document. The intended reference is likely 'Tab.~\ref{tab:action_interface}'.
- **[writing]** The caption for Figure 2 (method_loop) appears twice in the source (once in the main body, once in the appendix). Ensure only one instance remains to avoid duplicate figure numbering.
- **[writing]** In the 'Backbones' section (Appendix), the table caption refers to 'Table~\ref{tab:backbones}', but the label is defined inside the table environment. While often tolerated, ensure the label is placed immediately after \caption to guarantee correct cross-referencing.
