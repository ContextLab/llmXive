# Automated-review action items — Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Section 5.2 claims Code2LoRA Evo (64.5% IR EM) exceeds the per-repo LoRA (pLoRA) upper bound (64.2%). Since pLoRA trains on the target repo, exceeding it implies data leakage or a definition mismatch. Clarify how a generalization method beats a model trained on the exact target distribution.
- **[writing]** Section 5.3 notes OOD targets are shorter, inflating EM. The claim that Code2LoRA Evo leads by +1.8pp is valid, but the absolute EM gap (74.1% vs 72.3%) is confounded by length. Provide length-normalized metrics or clarify that the gap is a lower bound on true capability.
- **[writing]** Appendix A.4 states 'hallucinations/empty <1%'. With 2,321 errors, provide the exact count or percentage (e.g., 0.3%) to substantiate this quantitative claim. Vague bounds are insufficient for results sections.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption references 's static hypernetwork (b) and 's recurrent hypernetwork (c), but the model name is missing from the text, making the figure labels ambiguous.
- **[writing]** Figure 1: The 'Input' box contains a code snippet with a yellow highlight on '???', but the caption does not explain this visual cue or the specific task of assertion completion in detail.
- **[writing]** Figure 2: The caption references 'num-repos-total' as a variable rather than providing the actual count of repositories in the dataset.
- **[science]** Figure 2: The legend defines red dot area as proportional to '#QnAs', but the caption claims the figure illustrates 'Test-touching commits'; the figure fails to explicitly label the red dots as 'test-touching' or clarify if QnAs are the proxy for these commits.
- **[writing]** Figure 2: The x-axis label 'Commit date (first-parent)' is ambiguous; it is unclear if this represents the date of the first parent commit in a merge or simply the chronological date of the commit itself.
- **[science]** Figure 3: The left panel legend lists '4096 tokens' (orange dashed line), but no corresponding orange line is visible in the plot area, as the x-axis limit (4000) cuts it off. This creates a discrepancy between the legend and the visual data.
- **[writing]** Figure 3: The caption states that vertical dashed lines mark 'common context window sizes,' but the legend explicitly labels these lines with specific token counts (e.g., '512 tokens', '2048 tokens'). The legend should be updated to reflect that these lines represent specific context window thresholds rather than just generic sizes.
- **[fatal]** Figure 4: The caption contains broken text where method names are missing (e.g., 'of (Table checkpoints', 'and (median 66.7%)', 'for and'). The figure labels 'Code2LoRA-Static' and 'Code2LoRA-Evo' correspond to these missing names, but the caption fails to explicitly link them, making the specific performance claims unreadable.
- **[science]** Figure 4: The caption claims to report standard deviation (e.g., '=16.8') for the methods, but the symbol preceding the value is missing/blank in the text. Without the symbol (e.g., $\sigma$ or $SD$), the statistical metric is undefined.
- **[science]** Figure 5: The caption claims repositories with fewer than 50 training pairs 'frequently underperform the IR-test pretrained baseline (46.8%)', but the plot shows a dense cluster of points at 100% EM for N < 50, directly contradicting the text.
- **[writing]** Figure 5: The x-axis label '3 x 10^14 x 10^1' is malformed and unreadable; it likely intends to show a range (e.g., 3x10^1 to 4x10^1) but the formatting is broken.
- **[writing]** Figure 5: The legend entry 'N_train = 50' uses a dotted line style that does not match the vertical dotted line shown on the plot, creating ambiguity about what the line represents.
- **[science]** Figure 6: The caption claims performance improves 'log-linearly', but the left plot shows a log-linear fit (red dashed) with R²=0.721 and a power-law fit (green solid) with R²=0.719. The fits are nearly identical, and the data points show significant scatter (e.g., at 10^2 and 10^3 repositories), making the 'log-linear' claim weak and potentially misleading without statistical justification.
- **[science]** Figure 6: The right plot ('Error Rate Scaling') is not mentioned in the caption. The caption only describes 'CR-test EM as a function of training repository count', but the figure includes a second panel showing error rate, which is a different metric and should be described.
- **[writing]** Figure 6: The caption uses 'benefits from repository diversity' without specifying the method name (e.g., Code2LoRA), making it unclear which approach is being discussed. The method name should be explicitly stated.
- **[science]** Figure 7: The legend lists 'Code2LoRA' (blue dashed line with triangles) and 'Code2LoRA-Evo' (green solid line with stars), but the caption only describes the plot as 'CR-test exact-match vs. normalized commit position' without defining these specific method names or distinguishing between the 'Evo' and non-'Evo' variants.
- **[writing]** Figure 7: The legend uses inconsistent line styles to represent methods; 'Text2LoRA' is shown with a dash-dot line, 'Code2LoRA' with a dashed line, and 'Code2LoRA-Evo' with a solid line, but the legend markers (e.g., the dash-dot pattern for Text2LoRA) do not perfectly match the line styles in the plot area, potentially causing confusion.
- **[writing]** Figure 8: The colorbar label 'CR Test Exact Match (%)' is rotated 90 degrees and runs vertically along the axis, making it difficult to read; it should be horizontal or clearly legible.
- **[writing]** Figure 8: The text labels for individual repositories (e.g., 'django', 'pymc') are extremely small and densely packed, causing significant overlap and illegibility for many points.
- **[writing]** Figure 9: The top heatmap's y-axis labels include percentages (e.g., 'mkslides (12%)') that are not defined in the caption or figure; clarify what these percentages represent.
- **[science]** Figure 9: The bottom heatmap's colorbar scale (0.0–1.0) differs from the top heatmap's implied scale (0.0–1.0 but visually compressed); ensure consistent normalization or explicitly state if scales differ.
- **[writing]** Figure 9: The caption refers to 'FFT+DRC' in the bottom panel but does not define what FFT+DRC is; provide a brief explanation or cross-reference to its definition elsewhere in the paper.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'BPTT' (Backpropagation Through Time) at first use in Section 3.5 or Appendix B.1. Currently, the acronym appears without expansion, which excludes readers unfamiliar with recurrent training dynamics."
- **[writing]** Replace 'OOD' with 'out-of-distribution' at first mention in Section 1 and Section 5.3. The acronym is used frequently without prior definition, creating a barrier for non-specialist readers."
- **[writing]** Define 'DRC' (Dependency-Resolved Context) explicitly upon first introduction in Section 6 or Appendix B.1. The term is used as a proper noun without explanation, assuming reader familiarity with AST-based retrieval methods."
- **[writing]** Clarify 'CR' and 'IR' (Cross-Repo, In-Repo) in Section 1 or Section 5.1. While defined in a list, the acronyms are used immediately in the results summary without a clear 'hereafter referred to as' statement."
- **[writing]** Replace 'pp' (percentage points) with the full phrase 'percentage points' in Section 1 and Section 7.1. While common in statistics, it is jargon that should be spelled out for general accessibility."

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a compelling architecture for generating LoRA adapters via hypernetworks, but several logical gaps undermine the strength of the conclusions drawn from the experimental data. First, the claim in Section 3.1 and Table 1 that Code2LoRA-Static achieves an In-Repo (IR) Exact Match (EM) of 66.2%, effectively "matching" the per-repo LoRA (pLoRA) upper bound of 64.0% (or 64.2% in the evolution track table), is logically suspect. By definition, pLoRA is trained on the specific reposit

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** Claiming to exceed the 'per-repo LoRA upper bound' (Sec 5.2) is overreaching. Per-repo LoRA is trained on target data; claiming a cross-repo model beats it without qualification contradicts learning theory. Clarify if 'upper bound' refers to a specific constraint (e.g., time) or rephrase.
- **[science]** The claim that 'parametric adaptation outperforms context injection' (Sec 5.2) is too broad. Baselines use fixed retrieval params (k=3). Without testing optimal context injection, the paper cannot claim inherent superiority, only superiority over suboptimal baselines.
- **[science]** OOD generalization claims (Sec 5.3) are overstated. OOD targets are shorter (7 vs 12 chars), inflating EM. The paper admits this but still presents the EM lead as proof of robustness. Normalize metrics or temper the conclusion to address this confound.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Privacy and Content Review' section (Appendix) explicitly states 'No PII scrubbing performed.' Given the dataset includes full repositories with commit history, there is a non-negligible risk of inadvertently including sensitive data (API keys, credentials, or personal emails) scraped from public GitHub. Authors must add a statement confirming that a PII scan was performed or provide a mechanism for users to filter such data.
- **[writing]** The 'Potential risks' section (Limitations) is overly generic, stating risks 'mirror standard code LLMs.' The paper claims the model internalizes repository-specific conventions and identifiers. Authors should explicitly address the risk of the model memorizing and regurgitating proprietary code patterns or sensitive logic from the training repos, potentially facilitating IP leakage or security vulnerabilities in downstream applications.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The OOD evaluation (Table 3, Sec 5.3) is confounded by target length artifacts (median 7 chars vs 12-13). While the authors acknowledge this in the Limitations, the main results section claims a definitive lead (+1.8pp) without statistical significance testing or a length-normalized metric (e.g., EditSim) to isolate the model's generalization capability from the shorter answer bias.
- **[science]** The Evolution track training set (45,516 commits) is orders of magnitude larger than the Static track (409 repos). The paper does not provide a controlled ablation showing whether \codeloraevo{}'s superior performance stems from the GRU architecture or simply the massive increase in training data volume. A fair comparison requires matching the number of training examples or demonstrating performance saturation.
- **[science]** The claim that \codelorastatic{} matches the per-repo LoRA (pLoRA) upper bound on In-Repo tasks (66.2% vs 64.0% EM) is counter-intuitive and lacks rigorous statistical validation. Given the variance in per-repo performance (sigma=20.9% for pLoRA), the authors must report confidence intervals or a paired statistical test (e.g., Wilcoxon signed-rank) to confirm this is not a random fluctuation or overfitting artifact.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or effect sizes) for the reported performance gains (e.g., the +1.8pp OOD lead and +4.8pp CR lead). Without variance estimates or significance testing, it is unclear if these improvements are robust or due to random seed variance.
- **[science]** Clarify the experimental protocol for hyperparameter selection. The paper reports best checkpoint selection by 'CR-val loss' but does not specify if the test set was used for any tuning or if a strict hold-out validation set was maintained throughout. Ensure the test set was never used for model selection to prevent data leakage.
- **[science]** The OOD evaluation section explicitly notes that target lengths are shorter in the OOD set, inflating Exact Match (EM) scores. However, the primary claim of superiority relies on EM. Provide a re-analysis of the OOD results using length-normalized metrics (e.g., EditSim or CodeBLEU) as the primary comparison to ensure the conclusion is not an artifact of the target length distribution shift.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Results), the text repeatedly uses LaTeX macros (e.g., \UseMacro{cr-em-codelorastatic}) instead of resolved numeric values. This renders the prose unreadable and prevents verification of claims. Replace all such macros with their actual numeric values before final submission.
- **[writing]** The manuscript contains duplicate sections. Section 6 (Results) and Section 7 (Conclusion) appear in the main body, but identical or near-identical content (including Results, Conclusion, Limitations, and Dataset Details) is repeated in the Appendix (Sections starting at e002). Consolidate these into a single, coherent flow to avoid redundancy.
- **[writing]** In the Appendix (e001), the text describes Figure 1 (architecture) but the label `\label{fig:architecture_evo}` is placed after a paragraph of text rather than immediately following the figure environment or caption, which may cause reference errors in the compiled PDF.
