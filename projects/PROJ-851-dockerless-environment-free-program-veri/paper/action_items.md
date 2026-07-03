# Automated-review action items — Dockerless: Environment-Free Program Verifier for Coding Agents

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify in Section 3.2 if the score r_phi is derived from logits of generated tokens or a classification head to align the 'binary token' claim with the softmax formula.
- **[writing]** In Section 4.1, clearly distinguish between the Qwen3.5-9B baseline improvement (2.4 pts) and the SWE-Lego-8B specialist improvement (20.8 pts) to avoid conflating the two claims.
- **[writing]** In Section 3.2, specify if '3.7K issues' refers to the source pool or the final training set size after rejection sampling to avoid overstating the labeled data volume.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1 caption: The sentence 'instead deeply explores the codebase...' is missing the subject (the method name 'Dockerless'), making it grammatically incomplete and unclear.
- **[writing]** Figure 1 caption: The phrase 'LLM scorers sidestep that cost' is ambiguous; the diagram shows the LLM Scorer lacks a repository ('No Repo'), but the text should explicitly state it lacks repository grounding to match the visual.
- **[writing]** Figure 2 caption: The phrase 'Architecture of .' is missing the model name (likely 'Dockerless'), rendering the sentence grammatically incomplete.
- **[writing]** Figure 2 caption: The score notation 'r_(x, y)' uses incorrect LaTeX syntax; it should likely be formatted as $r_\phi(x, y)$ to match the visual label in the figure.
- **[science]** Figure 3: The caption states that 'hatched extensions (w/o Env) show the additional gain from per-repository environments,' but the legend labels the hatched pattern as 'w/o Env' (without environment). This contradicts the caption's claim that the hatched portion represents the gain from *using* environments (implying the full bar is 'with env'). The label 'w/o Env' on the hatched segment suggests it represents the 'without environment' condition, which conflicts with the caption's explanation t
- **[writing]** Figure 3: The caption contains a typo: 'hatched extensions (w/o Env) show the additional gain from per-repository environments' is confusingly phrased. It should clarify that the hatched portion represents the *difference* between env-based and env-free scores, but the label 'w/o Env' on the hatched bar is misleading given the caption's description.
- **[writing]** Figure 4: The label 'Candidate Pathes' contains a spelling error; it should be 'Candidate Paths'.
- **[writing]** Figure 4: The caption contains a missing model name ('Training pipeline for :'), likely due to a formatting error where the model name was omitted.
- **[writing]** Figure 5: The caption contains multiple missing nouns where the model name 'Dockerless' should appear (e.g., 'pipeline for .', 'scored by .', 'uses as the per-rollout reward source'). The diagram itself labels the verifier as 'Dockerless', but the caption text is broken.
- **[writing]** Figure 6: The x-axis has non-uniform spacing between ticks (0, 1, 2, 4, 6, 8) which visually distorts the slope of the line segments, particularly between 2 and 4.
- **[writing]** Figure 6: The shaded region labeled 'sweet spot' spans x=2 to x=5, but the x-axis has no tick mark at 5, making the right boundary of the region ambiguous.
- **[writing]** Figure 7: The caption mentions 'three reward sources' but the chart only displays three bars without a legend or labels identifying which source corresponds to which bar (Dockerless, Test Execution, DeepSWE Verifier).
- **[science]** Figure 7: The x-axis scale (0 to 2500s) and bar lengths do not visually align with the provided numerical annotations (e.g., 2308s + 180s = 2488s, yet the teal bar ends near 2300s), suggesting the bars represent only the variable cost or the scale is misleading.
- **[writing]** Figure 8: The caption states the candidate patch resolves the issue, but the 'Dockerless' score (0.996) is not explicitly defined as a 'resolved' or 'pass' metric in the figure or caption, unlike the 'Execution Pass (1.0)' label on the Ground Truth bar.
- **[science]** Figure 8: The 'Similarity' bar (0.468) is shown as a result of the 'Similarity Check' on the candidate patch, but the figure does not clarify whether this low similarity is expected or problematic given the caption's claim that the candidate patch is valid.
- **[science]** Figure 9: The caption states 'Solid bars are env-free; hatched extensions show the additional gain from per-repository environments,' but the legend labels the hatched portion as 'w/o Env' (without environment). This directly contradicts the caption's definition that the hatched part represents the gain from using environments.
- **[science]** Figure 9: The caption claims 'full bar height equals the env-based score,' yet the hatched bars are visually shorter than the solid bars in several cases (e.g., DS-V3.2 Pro), implying the 'gain' is negative or the visualization logic is inverted relative to the text description.
- **[writing]** Figure 10: The bubble size legend is missing; the caption states 'Bubble size encodes the number of test instances per language,' but no scale or reference bubbles are provided to interpret the values.
- **[writing]** Figure 10: Axis labels lack units; the caption mentions 'resolve rate (%)', but the axes only show numbers (20–70) without a '%' symbol or explicit unit label.
- **[science]** Figure 11: The caption claims to show distributions for 'three reward sources', but the plot contains only a single filled area (likely the 'DeepSWE Verifier' from the legend) and no other curves or histograms to compare against.
- **[writing]** Figure 11: The legend lists 'DeepSWE Verifier', 'Test Execution', and 'Dockerless', but the plot only displays the data for 'DeepSWE Verifier', leaving the other two sources unrepresented.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'AUC' at first use in the Abstract and Section 2.1. While standard in ML, the paper targets a broader audience including those unfamiliar with ROC curves. Replace '14.3 AUC points' with '14.3 points in Area Under the Curve (AUC)' on first occurrence.
- **[writing]** Replace the acronym 'RFT' with 'rejection-sampling fine-tuning' or 'rejection fine-tuning' at its first appearance in Section 2.3. The text currently introduces 'Rejection-sampling fine-tuning (RFT)' but later uses 'RFT' without ensuring the reader has retained the definition, and the acronym is not defined in the Abstract where the concept is introduced.
- **[writing]** Define 'SFT' and 'RL' at their very first occurrence in the Abstract. The text currently uses 'supervised fine-tuning (SFT)' and 'reinforcement learning (RL)' in the first sentence, but the Abstract is often read in isolation. Ensure these are explicitly defined before being used as acronyms in subsequent sentences.
- **[writing]** Replace the acronym 'env-free' and 'env-based' with 'environment-free' and 'environment-based' at their first occurrence in Section 2.1. The text defines them as 'environment-free (env-free)' but the hyphenated acronyms are used heavily thereafter. Consider using the full terms or ensuring the definition is prominent, as 'env' is informal jargon.
- **[writing]** Define 'GRPO' at first use in Section 2.3. The text states 'optimize the model with GRPO' without spelling out 'Group Relative Policy Optimization' or providing a citation that defines it immediately. Non-specialists may not recognize this specific RL variant acronym.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is generally high, with clear causal chains from the problem definition (environment setup costs) to the proposed solution (agentic verification) and the resulting benefits (scalable post-training). However, there are two areas where the premises and conclusions require tighter alignment to avoid potential logical gaps. First, the central claim that the verifier is "environment-free" (Abstract, Sec 1) is slightly at odds with the training methodology describe

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The term 'fully environment-free' (Abstract) overclaims. The method uses shell tools and may execute developer utilities (Sec 4.1, App D.2). It is 'Docker-free' or 'setup-free', not execution-free. Refine terminology to avoid implying zero execution occurs.
- **[writing]** Claiming the model 'matches' environment-based performance (Abstract) is too strong. Table 1 shows deficits on Multilingual (50.0 vs 51.3) and Pro (35.2 vs 35.7). Use 'approaches' or 'comparable to' instead of 'matches' to accurately reflect the data.
- **[science]** The '14.3 AUC' gain (Abstract) relies on a custom benchmark (Sec 5.2) with unspecified distribution details. Add a limitation noting this margin may not generalize if the benchmark is not representative of the full SWE-bench distribution.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper describes an agentic verifier that executes shell commands (find, grep, rg) on arbitrary repositories (Sec 3.1, App B). While labeled 'read-only', the system lacks explicit safeguards against side-channel attacks or unintended file system interactions (e.g., via symlinks or race conditions). The authors must explicitly state the sandboxing measures (e.g., seccomp, container isolation) used to prevent the verifier from modifying or exfiltrating data from the target repositories.
- **[science]** The training data construction (App A.1) relies on 'execution-labeled' patches from SWE-Gym and Multi-SWE-RL. The paper does not address whether these datasets contain personally identifiable information (PII), proprietary code, or sensitive credentials that might be inadvertently exposed during the verifier's agentic exploration or included in the training corpus. A statement on data privacy and the exclusion of sensitive artifacts is required.
- **[writing]** The verifier is trained via rejection sampling on trajectories where the model's verdict matches the ground-truth test outcome (Sec 3.2). This process risks reinforcing biases present in the test suites (e.g., favoring specific coding styles or languages) without explicit mitigation. The authors should discuss potential biases in the training signal and how they ensure the verifier does not learn to favor specific demographic or stylistic patterns in code.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The verifier evaluation benchmark (Sec 4.2, Tab 2) uses 776 samples (500 Verified, 276 Multi-SWE). The paper claims a 14.3 AUC point gain over the strongest baseline (DeepSWE Verifier, 66.7 vs 81.0). Given the sample size, the standard error for AUC is non-negligible. The authors must report confidence intervals (e.g., 95% CI via bootstrapping) or statistical significance tests (e.g., DeLong's test) to confirm this gain is not due to random variance on a relatively small test set.
- **[science]** The RL training uses a group size of G=8 (Appx D.3) and averages M=2 independent verifier passes per rollout. With only 50 RL steps total, the effective number of gradient updates is extremely low. The paper lacks an analysis of the variance in the final resolve rates across different random seeds. Without multiple seeds, the reported 62.0% resolve rate could be an outlier, and the claim of 'matching environment-based post-training' is statistically weak.
- **[science]** The ablation study on the number of verification questions (Fig 5) shows performance fluctuation (79.6 at K=6 vs 81.0 at K=4) but does not provide error bars or standard deviations across the 500-sample benchmark. It is unclear if the drop at K=6 is statistically significant or within the noise of the evaluation metric. The conclusion that 'additional questions introduce noise' requires statistical backing.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 3.2 (Verifier evaluation), the paper reports AUC improvements (e.g., +14.3 points) without providing confidence intervals or statistical significance tests (e.g., DeLong's test) to confirm these gains are not due to random variance on the 776-sample benchmark.
- **[science]** Section 3.4 (Question ablation) and Figure 4 show performance fluctuations for K=6 and K=8. The text attributes this to 'redundant or noisy evidence' but lacks a statistical test (e.g., paired t-test or ANOVA) to confirm these drops are significant compared to K=4.
- **[science]** In Section 3.1, the claim that 'env-free SFT matches env-based SFT' relies on small absolute differences (e.g., 60.6 vs 60.0). The paper should report confidence intervals for these resolve rates (likely via bootstrapping over the benchmark instances) to demonstrate statistical equivalence rather than just point-estimate proximity.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.2 (Architecture), the text states 'convert the logits... into a continuous score' followed by a softmax formula. However, the LaTeX source contains a commented-out block with a reviewer note: '\gu{this formular is hard to understand}'. The authors should either clarify the formula in the main text or remove the comment to ensure the final manuscript is clean and the math is clearly explained.
- **[writing]** In Section 2.3 (Training), the text mentions 'We additionally cap the negative-to-positive sample ratio at $\rho$'. The symbol $\rho$ is introduced but never defined with a specific value or range in the main text. While details may be in the appendix, the main text should define this hyperparameter (e.g., 'at $\rho=4$') to ensure the method is self-contained.
- **[writing]** In Section 3.2 (Verifier evaluation), the text states 'improves by $5.1$ and $8.2$ points, respectively' when comparing to the strongest frontier LLM judge. However, the table shows GPT-5.4 at 75.9 (Verified) and 59.5 (Multi-SWE). The calculation for Multi-SWE is 72.1 - 59.5 = 12.6, not 8.2. The text claims 8.2, which contradicts the table data. This numerical inconsistency must be corrected.
- **[writing]** In Section 3.4 (Latency analysis), the text says 'reward evaluation adds only $41$--$180$s'. The figure caption for Fig 5 (latency-overhead) is empty in the source ('\caption{Per-rollout wall-clock breakdown...}'). The caption should be completed to describe the figure content clearly, as the text relies on it for context.
