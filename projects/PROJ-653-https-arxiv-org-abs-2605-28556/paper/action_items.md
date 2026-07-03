# Automated-review action items — A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In the Abstract and Section 5.1, the claim that Gemini-3-Flash drops from '0.82–0.94' to '0.28–0.61' is misleading. Table 1 shows the 0.82–0.94 range applies only to the GPT-5.2 user simulator, while the 0.28–0.61 range applies to the Gemini-3-Flash user simulator. The text implies a single agent performance range across both conditions, conflating the user simulator variable. Clarify that these are distinct experimental conditions.
- **[writing]** Section 5.2 claims 'Weighted edit distance (WED) increases up to 124%'. Table A1 shows the Airline domain WED intra increases from 3.76 to 8.42 (124%), but the Retail domain increases from 4.89 to 7.07 (44%) and Telecom from 6.63 to 7.05 (6%). The claim 'up to 124%' is technically true but omits that this is domain-specific. Specify that the 124% figure applies specifically to the Airline domain to avoid overgeneralization.
- **[writing]** Section 5.3 states 'The verifier agent attains precision 1.0 (Airline) / 0.97 (Retail) and recall 0.75 / 0.83'. The text does not specify the denominator for recall (e.g., total valid tasks vs. total generated tasks). Without this context, the recall metric is ambiguous. Define the base set used for calculating recall to ensure the claim is verifiable.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states the figure compares weighted vs. unweighted edit distance, but the image only displays one set of clusters (Cluster A, B, C) without a corresponding second panel for the unweighted comparison.
- **[writing]** Figure 1: The caption claims chips are colored by tool type (read, write, generic), but there is no legend or key provided in the figure to map the specific colors (yellow, pink, grey) to these categories.
- **[science]** Figure 2: The caption describes a 'Right' panel for 'Airline Tool Frequency', but the rendered image contains four panels (WED Gold, TTR Gold, WED Simulations, TTR Simulations) and lacks the described tool frequency distribution.
- **[science]** Figure 2: The caption mentions '$BV$ distribution' and 'Other domains in Figure .', but the chart labels use 'rBV' and 'Ours', and the cross-reference is broken/empty.
- **[science]** Figure 3: The y-axis lacks a label (e.g., 'Accuracy (%)') and the right panel's y-axis has no tick labels, making the absolute performance values impossible to read.
- **[science]** Figure 3: The caption mentions 'using 0.5 thresholds' but does not define the units or scale for the 'write ratio' x-axis categories (read-heavy vs. write-heavy), nor does it explain the 'middle band dropped' methodology.
- **[writing]** Figure 3: The red percentage values (e.g., '-36%') are placed directly on the bars without a legend or caption explanation defining what these deltas represent (e.g., relative drop from short/read-heavy baseline).
- **[fatal]** Figure 4: The caption contains broken LaTeX syntax ('$^2$-Bench', '$BV$') and missing variable names (e.g., 'unlike $BV$, is non-saturated'), making the text unreadable and the comparison subject undefined.
- **[science]** Figure 4: The bar chart labels use '$\tau$BV' and 'Ours', but the caption refers to '$BV$' and 'Verified'; the figure fails to explicitly define which domain corresponds to 'Ours' or 'Verified' in the visual legend.
- **[writing]** Figure 4: The caption references 'see .' with a missing citation number, failing to direct the reader to the specific figure or section quantifying the Type-Token Ratio (TTR).
- **[fatal]** Figure 5: The caption describes a 'Left' panel (n-gram Model) and a 'Right' panel (Task Evolution), but the rendered image contains only a single chart. The 'Task Evolution' data mentioned in the caption is missing.
- **[science]** Figure 5: The x-axis labels are inconsistent and confusing. The first group is labeled 'Uniform Iteration k=0', while subsequent groups are labeled 'k=400', 'k=800', and 'k=3000'. The 'Uniform' label does not fit the 'Iteration k' pattern, and the 'OFF/ON' labels under the bars are not defined in the caption or legend.
- **[writing]** Figure 5: The x-axis labels are rotated and crowded, making them difficult to read. The text 'Init C+ with n-grams from:' and 'Train with C-:' are placed awkwardly above the bars without clear pointers or grouping lines.
- **[fatal]** Figure 6: The caption states 'Per-tool relative frequency on the retail and telecom domains' and mentions 'each panel's legend', but the rendered image shows only a single panel (likely retail) and lacks the second panel (telecom) entirely.
- **[science]** Figure 6: The caption claims tools are 'ordered within each panel by task frequency', but the y-axis labels (e.g., 'get_order_details' at the top with highest frequency, 'list_all_product_types' at the bottom) appear to be ordered by frequency, yet the caption implies a comparison against a baseline (likely BV) which is not explicitly labeled in the legend or axis.
- **[writing]** Figure 6: The caption contains a placeholder 'comparing against ;' with a missing baseline name (likely 'BV' based on context from other figures), making the comparison unclear.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific jargon and undefined acronyms that hinder accessibility for a broader audience. In the Abstract, "TTR" is used without definition; it should be spelled out as "Type-Token Ratio" immediately. Similarly, "WED" appears in Section 4.2 without expansion; "Weighted Edit Distance" must be stated first. The term "medoids" is used frequently in Section 3.2 and the algorithms. While standard in clustering literature, it is not common knowledge outside that

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent methodology for generating benchmarks, but there are minor logical gaps in how specific claims are supported by the stated mechanisms. First, in Section 5 (TASTE), the authors list "Validity" as a target of Stage 1 (Tool Sequence Sampling). Logically, sampling diverse sequences does not ensure validity; validity is explicitly enforced in Stage 3 via the Verifier agent. The text implies the sampling stage contributes to validity, but the mechanism described (contrast

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The abstract and introduction claim 'severe drops' and that benchmarks are 'saturated' based on single-point estimates without statistical significance testing. The checklist explicitly admits to reporting point estimates without error bars due to cost. The paper must temper claims of 'saturation' to reflect that the observed drops, while large, are not statistically validated against variance.
- **[writing]** The paper claims TASTE 'doubles coverage' (Abstract, Section 5.2) based on metrics like WED (+124%) and TTR (+111%). However, the baseline is a specific subset of tau-Bench (Verified). The claim of 'doubling coverage' implies a general property of the new benchmark, but the data only supports a comparison against this specific baseline. The scope of the claim should be restricted to the specific comparison made.
- **[writing]** The conclusion states TASTE 'could also generate training data.' This is a speculative extrapolation beyond the paper's scope, which focuses exclusively on benchmark construction and evaluation. The paper provides no data on model performance improvements when trained on TASTE-generated data. This forward-looking claim should be removed or clearly labeled as future work.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The NeurIPS Checklist (Section e001) marks 'Broader impacts' and 'Safeguards' as NA. Given the paper's explicit goal of generating 'adversarial' tasks (e.g., 'DB-grounded misdirection', 'policy enforcement') to degrade agent performance, a discussion on dual-use risks is required. Specifically, address how this methodology could be misused to generate training data for agents designed to bypass safety filters or exploit system vulnerabilities.
- **[writing]** The 'Verifier agent' and 'Evolution' stages rely on LLMs to generate 'decoy records' and 'adversarial patterns' (Section 4.3, Algorithm 3). The paper states these are validated but does not detail safeguards against the generation of harmful content (e.g., PII, hate speech, or instructions for illegal acts) within the synthetic task scenarios. A statement confirming the implementation of content filters or manual review protocols for generated task text is needed.
- **[writing]** The paper reports evaluation costs of $725 for generation and $520 for evaluation (Section 5). While not a direct safety violation, the reliance on expensive API calls for generating adversarial benchmarks creates a barrier to entry that limits independent verification of safety claims. The authors should explicitly discuss the reproducibility of their safety/validity checks for the broader community given these resource constraints.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 reports single-point estimates without confidence intervals. Re-run evaluations with multiple seeds (n>=5) per task or provide bootstrap CIs to validate that performance drops are not due to stochasticity.
- **[science]** The LLM-based Verifier has 0.75 recall, risking invalid tasks. Provide a human audit of a random sample of accepted/rejected tasks to confirm the ground truth validity of the benchmark.
- **[science]** Difficulty is defined by LLM failure, risking noise artifacts. Include a human baseline on a subset of evolved tasks to ensure difficulty is structural, not a generation artifact.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Section 5 report point estimates for agent performance without confidence intervals or standard errors. Given the stochastic nature of LLM outputs and the single-run evaluation per task, statistical significance of the reported performance drops (e.g., -52.8%) cannot be assessed. Please add error bars (e.g., via bootstrapping over tasks or multiple seeds) or explicitly state the limitation regarding statistical significance in the checklist and text.
- **[science]** The NeurIPS Checklist (Item 7) explicitly states 'Answer: No' for statistical significance due to API costs. However, the paper makes strong comparative claims (e.g., 'severe drops') based on single-point estimates. To support these claims scientifically, the authors must either provide variance estimates (e.g., 95% CIs) or reframe the results as descriptive statistics without implying statistical superiority/difference.
- **[science]** The clustering method (K-medoids) uses a weighted Levenshtein distance with fixed substitution costs (0.33, 0.66, 1.0). The sensitivity of the resulting medoids and subsequent task coverage to these specific weight choices is not analyzed. A brief ablation or justification for these weights would strengthen the statistical validity of the diversity claims.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, the notation '$K\!=50/114/114$' is ambiguous. Clarify which value corresponds to which domain (Airline, Retail, Telecom) to prevent reader confusion.
- **[writing]** Section 5 (Results) and the Abstract contain dense numerical ranges (e.g., '0.82-0.94 -> 0.28-0.61'). Ensure the text explicitly states whether these ranges represent performance across different user simulators or task subsets to avoid misinterpretation.
- **[writing]** The phrase 'reverse task construction' in the Introduction and Section 2 is slightly informal. Consider rephrasing to 'invert the task construction paradigm' or 'reverse the standard task generation pipeline' for greater academic precision.
- **[writing]** In Section 3, the definition of the reward function uses the symbol '$\equiv$' for state equivalence. Ensure this notation is defined or standard in the context of the paper, or use '$=$' if the states are strictly identical, to avoid ambiguity.
