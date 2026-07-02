# Automated-review action items — Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Kotlin: 71.0 > 63.4 The claim that Qwen3 is stronger on Python is also supported (85.6 vs 71.1). The evidence is consistent with the text. However, the text describes the gaps as "substantial" but does not quantify the magnitude (e.g., the 28.6 point gap in Rust). While not a factual error, the lack of quantification weakens the evidentiary support for the "substantial" descriptor. 2. Verification of Reproduction Accuracy (Section 4.2): The claim "mean absolute deviation is only about 3%" relies
- **[writing]** Visible data: Qwen3 (|−0.1| = 0.1), DeepSeek (|−2.4| = 2.4).
- **[writing]** The average of just these two is 1.25%, which is not "about 3%".
- **[writing]** The claim cannot be verified without the omitted rows. If the omitted rows contain larger deviations (e.g., >4%), the average could reach 3%. As written, the claim is unsubstantiated by the visible evidence. The authors must either include the full data or explicitly calculate and report the mean from the full set to support the "3%" figure. 3. Verification of Contamination Claims (Section 4.3): The text states: "Our main comparisons restrict evaluation to tasks released on or after 2025-02-01..
- **[writing]** There is a logical tension here. If the main results are restricted to post-2025-02-01, Figure 4 (showing trends) must include pre-2025-02-01 data to demonstrate the "higher scores on earlier months."
- **[writing]** The text does not explicitly clarify that Figure 4 includes data *outside* the main evaluation window. This ambiguity risks misrepresenting the scope of the main results. The claim of contamination is valid if the figure includes pre-cutoff data, but the text fails to clearly delineate the data scope of the figure versus the main tables. 4. Verification of Citation Dates (Appendix): Table tab:lang-2025-en cites "RedMonk Language Rankings, January 2025 (published June 2025)".
- **[writing]** RedMonk rankings are typically released bi-annually (e.g., Jan/July or similar). A "January 2025" ranking published in "June 2025" is an unusual lag and potentially a hallucinated citation detail.
- **[writing]** Given the paper's context (2026), citing a 2025 survey is normal, but the specific date mismatch (Jan data, June pub) requires verification. If this date is incorrect, the claim of "2025 popularity rankings" based on this specific source is factually flawed. Conclusion: The paper contains strong evidence for its primary performance claims, but specific numeric summaries (the 3% deviation) and citation details (RedMonk dates) lack sufficient verification in the provided text. The ambiguity regard

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The rendered image displays only the AtCoder logo and text, failing to show the 'Multi-LCB overview' pipeline (conversion, prompting, execution) described in the caption.
- **[fatal]** Figure 1: The caption text is truncated at the end ('produce equi') and references a missing image file '[logo_atcoder.png]', indicating a rendering or upload error.
- **[writing]** Figure 2: The x-axis labels are rotated and crowded, making the distinction between 'Overall', 'LeetCode', and 'AtCoder' columns difficult to read for each language block.
- **[writing]** Figure 2: The y-axis model names are not vertically aligned with their corresponding heatmap rows, creating ambiguity about which row belongs to which model.
- **[writing]** Figure 3: The x-axis labels are rotated 45 degrees and overlap significantly, making the 'LeetCode' and 'AtCoder' sub-labels difficult to read.
- **[writing]** Figure 3: The y-axis model names are truncated or cut off on the left side (e.g., 'Qwen3-235B-A22B-Thk-2507*' is partially obscured), reducing readability.
- **[writing]** Figure 4: The x-axis labels are rotated 45 degrees and overlap significantly, making them difficult to read; consider horizontal alignment or increased spacing.
- **[writing]** Figure 4: The y-axis model names are crowded and some are truncated or hard to distinguish due to tight vertical spacing; consider increasing row height or using a scrollable format.
- **[science]** Figure 4: No error bars or confidence intervals are shown despite Pass@1 being a statistical metric; the caption does not mention whether values are means, medians, or single runs.
- **[science]** Figure 6: The x-axis labels (e.g., 'RUBY Overall', 'RUBY Easy') contradict the caption's claim that the figure shows 'difficulty-specific results (LeetCode vs AtCoder)'; the figure displays difficulty levels, not platforms.
- **[writing]** Figure 6: The x-axis labels are rotated at a steep angle and overlap significantly, making them difficult to read; consider horizontal alignment or better spacing.
- **[science]** Figure 7: The x-axis labels (Overall, Easy, Medium, Hard) contradict the caption's claim that the figure shows 'platform-specific results (LeetCode vs AtCoder)'; the figure displays difficulty levels, not platforms.
- **[writing]** Figure 7: The title 'Difficulty Metrics Heatmap - Group 3' is inconsistent with the caption's description of 'Code generation performance heatmap by difficulty level'.
- **[science]** Figure 8: The legend lists model names with future dates (e.g., 'Qwen3-235B-A22B-Thinking-2507*', 'Qwen3-30B-A3B-Thinking-2507*') that do not align with the x-axis timeline (2023-2025), suggesting hallucinated or erroneous model identifiers.
- **[science]** Figure 8: The x-axis extends to '2025-05', but the data lines terminate abruptly at '2025-04' or earlier, leaving the final tick mark without corresponding data points.
- **[science]** Figure 9: The legend lists model names with asterisks (e.g., 'Qwen3-235B-A22B-Thinking-2507*') and specific version numbers (e.g., '2507') that do not align with the paper's title 'Multi-LCB' or the provided context, suggesting these are hallucinated or placeholder labels rather than actual evaluated models.
- **[writing]** Figure 9: The x-axis labels are rotated 45 degrees and overlap significantly, making the timeline difficult to read; increasing the figure width or reducing label density is recommended.
- **[science]** Figure 10: The legend lists 10 models, but the plot contains 11 distinct lines (e.g., two red lines, two green lines, two dark red lines), making it impossible to map all data series to their labels.
- **[writing]** Figure 10: The x-axis label 'Year-Month' is rotated 45 degrees, causing the tick labels (e.g., '2023-04', '2023-05') to overlap and become difficult to read.
- **[science]** Figure 11: The legend lists 11 models, but the plot contains 12 distinct lines. Specifically, the red line starting in 2025-02 (likely 'Qwen3-14B*' from the legend) has no corresponding legend entry, making it impossible to identify the model.
- **[writing]** Figure 11: The x-axis labels are rotated 45 degrees and overlap significantly, making the dates difficult to read. A horizontal layout or staggered alignment would improve legibility.
- **[science]** Figure 12: The legend lists 11 models, but the plot contains 12 distinct lines (e.g., two red lines, two green lines, two orange lines). The legend fails to distinguish between the base models and their variants (e.g., 'Qwen3-235B-A22B*' vs 'Qwen3-235B-A22B-Instr-2507'), making it impossible to map specific lines to model names.
- **[science]** Figure 12: The x-axis extends to '2025-05', but data points stop abruptly around '2025-04' for most series, with some ending earlier (e.g., '2025-02'). The timeline implies future data or a mismatch between the axis range and the actual data collection period.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript demonstrates a strong command of the specific subfield of LLM code evaluation but occasionally relies on jargon that may exclude readers from adjacent disciplines (e.g., general NLP, software engineering, or data science). In the Introduction, the term "contamination-aware" is used as a compound adjective without prior definition. While the concept is explained in the following sentence, the term itself acts as a barrier. Similarly, "functional format" (Section 3) is used to descr

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3 claims conversion validity based on inspecting ~500 tasks, yet the benchmark evaluates 1,055 tasks per language. The sample size is insufficient to logically support the conclusion that the conversion is error-free across the entire dataset and all 12 languages.
- **[writing]** Section 5 asserts a universal Python bias ('above diagonal') while citing a model outperforming on six non-Python languages. The logic connecting this specific counter-example to the general trend is unclear without defining the 'Average' metric precisely.
- **[science]** The claim that 'lack of multi-language training' causes performance gaps is unsupported. The paper does not control for model size or architecture, so the gap could stem from data scarcity rather than training strategy.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of 'Language-specific contamination' (Intro, item 3) lacks statistical evidence. The paper attributes performance drops to contamination but provides no correlation analysis between model cutoff dates and task release dates per language to distinguish this from inherent difficulty. Re-analysis or removal is required.
- **[writing]** The conclusion that 'Python is not always a reliable proxy' (Intro, item 1) overgeneralizes. Data shows strong correlation for top-tier models (e.g., Qwen3-235B scores 85.6% Python vs 86.6% C++ in Table tab:multi_lcb_1055), contradicting the 'substantial gaps' narrative for the frontier. Qualify this claim to apply only to specific model classes.
- **[science]** The assertion that 'Automatic conversion... may alter task complexity' (Limitations) is unquantified. If conversion introduces language-specific bias, observed gaps may be artifacts of benchmark construction rather than model capability. Provide an ablation study on conversion fidelity or retract the claim that gaps reflect 'structural challenges' of the languages.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[fatal]** The 'Legal Compliance and License' section (Appendix A) asserts Fair Use and CC BY-NC 4.0 licensing for data derived from LeetCode, AtCoder, and Codeforces. This requires explicit confirmation that the original platforms' Terms of Service permit such derivative benchmarking and redistribution. Authors must cite specific ToS clauses or obtain legal clearance to avoid copyright infringement risks.
- **[science]** The evaluation pipeline executes untrusted code generated by LLMs in a sandbox (Section 4). While network access is disabled, the paper lacks details on resource exhaustion protections (e.g., fork bombs, infinite loops consuming all memory) beyond the stated 6s/4GB limits. Authors should describe the specific isolation technology (e.g., gVisor, Firecracker) and confirm it prevents host compromise.
- **[writing]** The dataset includes problems from competitive programming platforms. Authors must explicitly state whether they obtained consent or ethical clearance for using these problems in a public benchmark, particularly if the problems contain user-generated content or if the platforms' policies restrict automated scraping and redistribution.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Section 4.1 claims 'Pass@1 averaged on 10 runs' but does not report the standard deviation or confidence intervals for the cross-language comparisons. Without error bars or statistical significance tests (e.g., paired t-tests) for the reported gaps (e.g., the 60% vs 30% disparity), the claim of 'substantial performance gaps' lacks statistical rigor.
- **[science]** The 'Python overfitting' claim (Section 1, Item 2) relies on a visual inspection of Figure 2 (scatter plot). The text states 'Almost every point lies above the x=y diagonal' but does not quantify the correlation coefficient or provide a statistical test to rule out that the observed bias is due to random variation or dataset difficulty differences rather than model overfitting.
- **[science]** The conversion of LeetCode functional tasks to STDIN/STDOUT (Section 3) is described as 'automatic' with 'no inconsistencies found in 500 tasks.' However, the sample size (500) is not defined relative to the total task pool (1,055 per language). A formal validation of the conversion pipeline's fidelity across the full dataset is required to ensure the benchmark does not introduce artificial difficulty or bias in non-Python languages.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 4.1 reports Pass@1 averaged over 10 runs with standard deviations (e.g., 71.1 ± 2.1). However, the statistical significance of the observed performance gaps between languages (e.g., Python vs. Scala) is not assessed. Given the binary nature of Pass@1, authors should report confidence intervals (e.g., Wilson score intervals) or perform paired statistical tests (e.g., McNemar's test) to validate that the reported disparities are not due to random variance in the 10 runs.
- **[science]** The claim of 'Python overfitting' relies on visual inspection of Figure 2 (scatter plot) and the observation that points lie above the x=y diagonal. The manuscript lacks a formal statistical test (e.g., a paired t-test or Wilcoxon signed-rank test) comparing Python scores against the mean of non-Python languages for each model to substantiate the claim that the bias is statistically significant rather than anecdotal.
- **[science]** In Section 4.2, the comparison with LiveCodeBench reports a 'mean absolute deviation' of ~3% but does not provide a confidence interval for this deviation or a test of equivalence. To rigorously claim that the multilingual transformation introduces 'no artificial difficulty,' a statistical equivalence test or a tighter bound on the difference (e.g., 95% CI of the mean difference) is required.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the double-URL typo in Table 1 (e002) where 'https://https://huggingface.co' appears for gpt-oss models. This is a clear copy-paste error that breaks the link.
- **[writing]** Fix the inconsistent label reference in Section 5.1: the text cites 'Figure \ref{fig:python_vs_all_pass1_ellipces}' but the label defined in the code is 'fig:python_vs_all_pass1_ellipces' (missing the 's' in 'ellipces' vs 'ellipses' in the caption). Ensure the label matches the intended figure name.
- **[writing]** Standardize the capitalization and spacing in the 'Languages errors type' section title (e001). It currently reads 'Languages errors type' which is grammatically awkward; suggest 'Error Types by Language' or 'Language-Specific Error Types'.
- **[writing]** In Section 3 (Benchmark Design), the phrase 'In our manual inspection of approximately 500 tasks, we did not find cases where language-dependent features introduced inconsistencies' is slightly wordy. Consider tightening to 'Manual inspection of ~500 tasks revealed no inconsistencies arising from language-dependent features.'
