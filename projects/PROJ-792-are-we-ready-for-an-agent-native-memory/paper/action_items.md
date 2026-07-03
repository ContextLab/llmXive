# Automated-review action items — Are We Ready For An Agent-Native Memory System?

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1 (Introduction) claims '2026' as a current year for citations (e.g., luo2026data, openai2026agents). As the paper is a preprint (arXiv:2606.24775), these future-dated citations are factually impossible unless they refer to unreleased internal roadmaps. Verify if these are typos for 2024/2025 or if the paper relies on hallucinated/future-dated sources.
- **[writing]** Section 1 claims '12 representative memory systems' are evaluated, but Table 1 lists 13 distinct systems (MemoChat, Mem0, MEM1, MemAgent, MemTree, Zep, Mem0^g, Cognee, LightMem, SimpleMem, MemOS, MemoryOS, A-MEM). The count in the text does not match the evidence in the table.
- **[writing]** Section 4.1 (RQ1) states 'Long Context achieves 48.20 EM on DB-Bench', but the text immediately before says 'MemoChat leads DB-Bench (55.40 Task Success Rate)'. The claim conflates 'Exact Match' (EM) with 'Task Success Rate' (TSR) metrics, attributing the EM score to the wrong system or metric type without clarification.
- **[writing]** Section 4.3 (RQ3) Table 3 lists 'Long Context' with 8.1 EM on LoCoMo, but the text in Section 4.4 (RQ4) claims 'Long Context drops (42.6 -> 19.0)' on LongBench. The baseline performance values for 'Long Context' vary significantly across sections (8.1 vs 42.6) without explaining if these are different datasets or different experimental setups, creating ambiguity in the comparative claims.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The legend at the top (Memory Represent. & Storage, Memory Extraction, etc.) uses colored boxes that do not match the shapes or colors used in the diagrams below (e.g., 'Memory Extraction' is a green box in the legend but green hexagons in the figure). This creates ambiguity about which components belong to which category.
- **[writing]** Figure 1: The legend labels are truncated (e.g., 'Represent. & Storage' instead of 'Representation & Storage'), reducing clarity and professionalism.
- **[science]** Figure 1: In panel (a), the 'Reflection (LLM)' and 'Planner (LLM)' components are gray hexagons, but they are not defined in the legend or caption — it’s unclear whether they fall under 'Memory Retrieval / Routing' or another category.
- **[writing]** Figure 2: The caption is marked '(to be refined)' and lacks specific details about the datasets, metrics, or experimental conditions shown in the plot.
- **[science]** Figure 2: The x-axis uses a logarithmic scale (1, 3, 10, 30, 100, 300) but lacks explicit tick labels or grid alignment for intermediate values, making precise reading of runtime difficult.
- **[writing]** Figure 2: The legend 'Double-outline = Pareto-optimal' is present, but the term 'Pareto-optimal' is not defined in the caption, leaving the criteria for optimality ambiguous.
- **[fatal]** Figure 3: The caption describes a two-panel figure ((a) comparison, (b) trending), but the image shows only a single scatter plot.
- **[science]** Figure 3: The x-axis label 'Sum of Mean Build+Query Runtime Across 3 Tasks (s)' is ambiguous; it is unclear if the values represent the sum of means or the mean of sums.
- **[writing]** Figure 3: The legend 'Double-outline = Pareto-optimal' is a text box rather than a standard legend, and the term 'Pareto-optimal' is not defined in the caption.
- **[science]** Figure 9: The x-axis labels in subplots (a)-(d) are rotated 45 degrees, causing the text to be illegible and unreadable.
- **[science]** Figure 9: Subplots (a)-(d) lack a y-axis title (e.g., 'Score' or 'Percentage'), making the metric units ambiguous despite the caption.
- **[science]** Figure 9: The legend at the top ('Reference Baselines', 'Sequential Context', etc.) does not map to the specific x-axis categories (e.g., 'Mem0', 'Cognee') shown in the plots, leaving the grouping logic unclear.
- **[science]** Figure 10: The legend lists 'Zep Local' (red square), but the bar chart in panel (a) labels the corresponding red bars as 'Zep MemTree', creating a direct contradiction between the legend and the chart labels.
- **[science]** Figure 10: Panel (a) bar chart x-axis labels are cluttered and overlapping (e.g., 'Zep MemTree', 'LightMem SimpleMem'), making it difficult to distinguish which bar belongs to which method.
- **[writing]** Figure 10: The legend in panel (b) uses inconsistent line styles (solid, dashed, dotted, dash-dot) and markers that are difficult to distinguish visually in the plot, reducing readability.
- **[science]** Figure 11: The x-axis labels ('Emb. RAG', 'LightMem', 'MemOS', 'MemTree', 'A-MEM') describe specific memory systems, but the caption states the figure is an 'Ablation of Backbones'. This indicates a mismatch between the figure content and its caption, suggesting the wrong plot was rendered or the caption is incorrect.
- **[writing]** Figure 11: The numerical data labels on top of the bars are extremely small and illegible, making it impossible to read the precise values without zooming in significantly.
- **[science]** Figure 12: The legend in panel (b) lists 12 methods, but the x-axis only has 4 bins. The lines are extremely cluttered and overlapping, making it impossible to distinguish individual method trends or verify the 'growth' claim for specific systems.
- **[writing]** Figure 12: Panel (a) x-axis labels are split across multiple lines (e.g., 'Long Ctx', 'Embed RAG'), which is visually cluttered and reduces readability compared to a single-line label.
- **[science]** Figure 12: Panel (c) y-axis is 'Answer F1 (%)' while panel (b) is 'ROUGE-L F1 (%)'. The caption describes (c) as 'Temporal evidence-distance drift' but does not clarify if the metric change is intentional or if it should be consistent with (b) for comparison.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript suffers from a moderate density of unexplained jargon and acronyms that creates a barrier for readers outside the immediate sub-field of LLM retrieval optimization. While the paper aims for a "data management perspective," it frequently relies on specific LLM implementation details (e.g., "KV-cache," "RLGF") and retrieval algorithm acronyms ("RRF," "MMR") without defining them at first use. Specifically, in Section 3.1.1 and 3.1.2, terms like "KV-cache" and "KV tensors" are used a

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 4.3, the claim that "graph-based methods handle updates reliably" overgeneralizes the data. Table 2 shows Zep leads in Knowledge Update, but Cognee (also graph-based) lags there while leading in Temporal Reasoning. The causal link between "graph-based" and "reliable updates" is not uniform; specify the mechanism (e.g., multi-versioning) driving Zep's success.
- **[writing]** In Section 5.2, the conclusion that "broad extraction preserves answerability" ignores that MemOS Fine outperforms Fast on LongMemEval (22.3 vs 20.7 EM). The claim is only supported for LoCoMo. Qualify the conclusion to reflect that broad extraction is superior for conversational recall but selective extraction may be better for factual precision.
- **[writing]** In Section 4.5, the paper cites Cognee's high latency (116.5s) as a "high-utility" example while advocating for "localized maintenance" as the most cost-efficient rule. The text fails to logically reconcile why a high-cost system is highlighted as a positive example without explicitly stating the specific workload conditions where such cost is justified.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The title asks 'Are We Ready?', implying a definitive readiness assessment, but the conclusion states 'no single architecture dominates' and effectiveness is 'workload-dependent'. The paper over-claims a readiness verdict without providing a clear, quantitative threshold for 'readiness' or a specific recommendation for production deployment.
- **[writing]** The abstract claims to evaluate '12 representative memory systems', yet Table 1 lists 13 distinct systems (MemoChat, Mem0, MEM1, MemAgent, MemTree, Zep, Mem0^g, Cognee, LightMem, SimpleMem, MemOS, MemoryOS, A-MEM). This discrepancy suggests either an unexplained exclusion or an over-claim of the evaluation scope.
- **[science]** The paper claims 'Raw long-context retrieval outperforms memory-backed approaches for time-dependent queries' (Introduction). However, Section 4.1 (O1) shows 'Long Context' achieving 48.20 EM on DB-Bench, while 'MemoChat' (a memory system) achieves 55.40 Task Success Rate. The claim of raw retrieval superiority is not universally supported by the presented metrics and over-generalizes the findings.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper evaluates 12 systems using LLMs for extraction and consolidation (e.g., Mem0, Zep, Cognee) but lacks an explicit discussion of privacy risks. Authors must address how PII (Personally Identifiable Information) is handled during the 'Schema-Constrained Extraction' phase, specifically whether data is redacted before storage or if the evaluation datasets contain sensitive user data that was not consented for this specific benchmarking.
- **[writing]** The evaluation relies on external datasets (e.g., LoCoMo, LongMemEval) and code hosted on GitHub. While external hosting is acceptable, the paper must explicitly state the data licensing terms and confirm that the datasets used for 'dynamic updates' and 'temporal reasoning' do not contain non-consensual personal data or copyrighted material that would violate ethical guidelines for redistribution or automated processing.
- **[writing]** The 'Memory Maintenance' section discusses 'Capacity-Driven Physical Eviction' and 'Semantic Consolidation.' The authors should briefly address the ethical implications of automated data deletion or summarization, particularly if these systems were deployed in real-world scenarios where 'forgetting' could lead to the loss of critical evidence or the erasure of user history without explicit user control.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims to evaluate 12 systems across 11 datasets but lacks a dedicated table or appendix listing the specific dataset-to-system mapping. Without this, the sample size and coverage of the experimental design cannot be independently verified.
- **[science]** Statistical significance testing is absent. The paper reports point estimates (e.g., 'Zep leads... 48.0') but provides no p-values, confidence intervals, or standard deviations to determine if observed differences (e.g., 48.0 vs 48.20) are statistically meaningful or noise.
- **[science]** The ablation studies (Section 6) modify components of specific systems (e.g., LightMem, MemOS) but do not explicitly state the number of random seeds or runs averaged for each reported metric. This omission prevents assessment of result stability and variance.
- **[science]** The 'Long Context' baseline is treated as a single data point in several comparisons (e.g., Table 3, Section 5.1) without clarifying if it represents a specific model configuration or an aggregate. The lack of variance metrics for this critical baseline weakens the comparative claims.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 4.2 (RQ2) and Table 1 (RQ3) report point estimates (e.g., 44.4, 36.8) without confidence intervals or standard deviations. Given the stochastic nature of LLM backbones and the small sample of systems (n=12), statistical significance of the reported differences (e.g., Zep vs. Cognee) cannot be assessed. Please report variance metrics or perform significance testing (e.g., bootstrap or t-tests) to support claims of superiority.
- **[science]** Section 4.5 (RQ5) and Section 5.4 (M4) discuss cost-performance trade-offs and maintenance strategies based on single-run latency/accuracy points. The analysis lacks error bars or variance analysis for latency measurements, which are critical for distinguishing between system noise and genuine architectural differences. Please include standard deviations or confidence intervals for all latency and utility metrics.
- **[science]** The ablation studies in Section 5 (Tables 2-4) modify single components but do not explicitly address multiple-comparisons correction. With numerous pairwise comparisons across 12 systems and multiple variants, the risk of Type I errors is elevated. Please clarify if corrections (e.g., Bonferroni, Holm) were applied or discuss this limitation in the context of the reported 'best' variants.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The LaTeX source contains duplicate section definitions. Section 'Preliminaries' (sec:def) appears in both e000 and e002 with conflicting content and table formatting. Section 'Memory Retrieval and Query Routing' (subsec:retrieval) is defined twice (in e001 and e003) with different text. This causes compilation errors and narrative confusion. Merge these sections into single, coherent definitions.
- **[writing]** In Section 1 (Introduction), the list of contributions uses inconsistent formatting. Items (1) and (2) use bold headers followed by parenthetical section references, while items (3) and (4) use bold headers followed by bolded questions. Standardize the structure for all four contributions to improve readability.
- **[writing]** Section 3.2 (Memory Retrieval Fidelity) and Section 3.5 (Memory Operation Cost) contain 'O1' and 'O7' labels respectively, but Section 3.3 (Memory Evolution Robustness) jumps to 'O4' and 'O5', and Section 3.4 (Long Horizon Memory Stability) uses 'O6'. The observation numbering is non-sequential and disjointed across subsections. Re-number observations globally (O1-O11) or per subsection to ensure logical flow.
