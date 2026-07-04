# Automated-review action items — NatureBench: Can Coding Agents Match the Published SOTA of Nature-Family Papers?

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a rigorous benchmarking framework, but several central claims rely on model names and statistics that do not align with current public reality or internal data consistency. First, the evaluation section (Section 4.1) and Table 1 list "GPT-5.5", "Gemini 3.5 Flash", and "Claude Opus 4.7" as evaluated agents. These model versions do not exist in the public record as of this review. Citing non-existent baselines for a "SOTA" comparison invalidates the core empirical claim that age

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The 'ML task family' bar chart contains a legend entry 'Tail 19' that is not represented by a visible bar in the chart, creating a mismatch between the legend and the data visualization.
- **[writing]** Figure 2: The 'Contribution type' bar chart uses colored dots to represent categories (Adapt, Imax, Form) but lacks a legend or key to define what these colors or symbols signify.
- **[writing]** Figure 3c: The caption text 'Per-task $$ in base versus reproduce mode' contains a rendering artifact ('$$') instead of the variable name (likely 'g'), making the description unreadable.
- **[science]** Figure 3c: The scatter plot lacks a legend defining the blue circles and red triangles, which are only identified by model names in the legend of Figure 3b; this forces the reader to cross-reference panels to understand the data series.
- **[writing]** Figure 4: The 'Source Journals' bar chart in the top-left panel lacks a visible x-axis or unit labels, making the numerical values (36, 26, 16, etc.) ambiguous without external context.
- **[writing]** Figure 4: The 'Agent Iterative Process' section at the bottom is not mentioned in the caption, which focuses on the pipeline construction and evaluation service rather than the agent's internal method evolution.
- **[science]** Figure 5a: The x-axis scale is misleading and inconsistent. The left side (negative gap) spans 0 to 80, while the right side (positive gap) spans 0 to 40. This compresses the visual representation of the 'Match or exceed SOTA' performance, making the blue bars appear smaller than they are relative to the red bars, which distorts the comparison of success vs. failure rates.
- **[writing]** Figure 5a: The y-axis labels are cluttered and difficult to read. Model names (e.g., 'Claude Opus 4.7') are stacked with sub-labels (e.g., 'Claude Code') in a way that creates visual noise and makes it hard to associate the correct bar with the correct model.
- **[science]** Figure 6b: The x-axis label '% of runs / Match-SOTA rate' is ambiguous and potentially misleading. The bars represent the percentage of runs within specific method-family categories (Same family vs. Alternative) that achieved Match-SOTA, not a rate normalized by the total number of runs. The label should clarify that these are conditional success rates (e.g., 'Match-SOTA rate within method family') to avoid confusion with the overall run distribution shown in Figure 6a.
- **[writing]** Figure 6c: The y-axis label 'Proxy prediction' is likely a misnomer or typo for 'Proxy-based prediction' or 'Proxy prediction method' to match the grammatical structure of the other categories (e.g., 'Search / tuning', 'Engineering pipeline'). While understandable, the phrasing is inconsistent with the other labels.
- **[writing]** Figure 7c: The y-axis label contains a LaTeX artifact 'Spearman $$' instead of the variable name (likely $ho$), and the axis lacks a title.
- **[writing]** Figure 7c: The y-axis label 'Opus 4.7' is rotated 90 degrees, making it difficult to read compared to the horizontal labels in other subplots.
- **[writing]** Figure 7c: The x-axis label 'Spearman $ho$' is present, but the y-axis label is missing the variable name, showing only 'Spearman $$'.
- **[science]** Figure 8b: The y-axis lacks a label and units, making the 'Relative gap' scale ambiguous for the genomic sequence prediction task.
- **[science]** Figure 8c: The x-axis labels ('Greedy', 'Beam') are not defined in the caption or legend, leaving the comparison between decoding strategies unclear.
- **[writing]** Figure 8: The green text 'crosses SOTA' in panel (a) is not defined in the caption or legend, making its meaning ambiguous.
- **[writing]** Figure 9: The caption states panel (a) shows 'eight biological networks', but the rendered image only displays seven bars (MTG, LTG, PCNet, Multinet, IRefindex v9, STRINGdb, CPDB, IRefindex v15).
- **[writing]** Figure 9: The caption states panel (b) shows '19 genomic sub-tasks', but the rendered image only displays 18 bars (Enhancers through H3K27ac).
- **[writing]** Figure 10: The caption lists six specific citations (e.g., miao2025multigate) for the source figures in panel (a), but the rendered image does not display these citations or labels, making it impossible to verify the mapping between the representative figures and the listed papers.
- **[writing]** Figure 10: The bar chart in panel (b) displays 'Surpass-SOTA (%)' on the y-axis, but the caption defines the metric as 'Surpass-SOTA ($g>0.1$)'. The figure should explicitly clarify if the percentage represents the proportion of tasks where $g>0.1$ or if the threshold differs from the caption's definition.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper is generally well-structured for a technical audience, but it relies on several acronyms and notation conventions that are introduced without explicit definition at their first point of use, which may stall a competent reader from an adjacent field (e.g., a computer vision researcher reading a systems paper, or vice versa). The most significant omissions are the acronyms "SOTA" (State-of-the-Art), "SR" (Score Rate), and "CR" (Completion Rate). While "SOTA" is ubiquitous in ML, the pape

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper's argument structure is generally sound, with clear premises leading to conclusions about agent capabilities. However, there are minor inconsistencies in the reporting of aggregate statistics that require clarification to ensure the logical flow from data to conclusion is unambiguous. In Section 5.1, the text states: "As shown in Fig.~\ref{fig:solution-mechanisms}a, the Match-SOTA rate of all agents is only $32.2\%$". This phrasing is ambiguous. Does it mean the average Match-SOTA rate

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Intro claim NatureBench is 'the first' to combine paper-sourced tasks, science, and optimization. Table 1 shows MLS-Bench also targets 'method invention' on research problems. Narrow the claim to 'first to use published SOTA anchors from Nature-family papers' to match the evidence.
- **[writing]** Abstract contrasts 'methodological translation' with 'genuine scientific invention,' but Section 5.1 only measures 'domain-reasoned alternatives' (8.3%) and 'method-aligned solutions' (9.0%). Rephrase to 'rather than proposing novel domain-specific methods' to avoid implying a measured category that doesn't exist.
- **[writing]** Conclusion states failures are 'not by task misunderstanding' (citing 3.1%). However, 'wrong method choice' (45.1%) can stem from misunderstanding. Soften to 'Failures are dominated by method selection and execution depth, with task misunderstanding being a minor factor' to match the data's granularity.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a benchmark (NatureBench) and pipeline (NatureGym) for evaluating AI coding agents on scientific discovery tasks derived from Nature-family publications. From a safety and ethics perspective, the work is low-risk and appropriately scoped.

The primary data sources are publicly available datasets and code repositories associated with peer-reviewed papers, which the authors explicitly state are accessed without authentication or special application (Section 2.2, Level 3). The pipeline includes a "file-level firewall" (Section 2.3) and an "information firewall" (Section 2.1) designed specifically to prevent the leakage of source methods or ground truth to the agents, thereby mitigating risks of data contamination or shortcut-taking rather than genuine discovery.

The evaluation protocol involves running agents in isolated Docker containers with a strict "web-search-disabled" policy (Section 4.1), preventing the agents from accessing external sensitive information or the original papers during the task. The benchmark tasks themselves are derived from published scientific literature and do not involve generating novel biological sequences, chemical compounds, or cyber-attack vectors that could be directly weaponized; the "discovery" is limited to optimizing code for existing, public scientific problems.

There is no use of private human-subjects data, PII, or sensitive health records; the datasets are aggregated scientific data (e.g., genomic sequences, protein structures, molecular graphs) that are already public. The paper does not describe any dual-use capabilities that lower the barrier to harm (e.g., automated vulnerability discovery or biological synthesis planning) beyond the general capability of coding agents, which is the subject of the benchmark itself. No conflicts of interest are apparent that would bias the safety assessment, and the authors disclose their affiliations clearly.

Consequently, there are no foreseeable, non-trivial risks of harm that are unacknowledged or unmitigated in this work. The paper does not require additional safety disclosures or mitigations.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a rigorous benchmarking framework, but the evidentiary strength of its central quantitative claims is weakened by a lack of variance reporting and potential confounds in the experimental design. First, the headline results in Table 1 (Section 4.2) are derived from single training/execution runs per agent-task pair. The paper reports that Claude Opus 4.7 surpasses SOTA on 17.8% of tasks, but provides no standard deviation, confidence interval, or seed count. In stochastic optim

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical treatment in this paper is generally sound in its descriptive reporting of the benchmark results, but it lacks inferential rigor in its comparative analysis sections. Specifically, in Section 5.1 ("Solution Mechanisms"), the authors compare Match-SOTA rates between two groups of runs (same method family vs. different family): 37.7% vs. 29.6%. While the descriptive difference is clear, the text asserts this as a finding ("These shifts are not equally effective") without reporting

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-written, with a clear narrative arc and precise technical descriptions. The prose is dense but largely free of grammatical errors or confusing syntax. However, there are minor instances of structural redundancy and slightly clunky phrasing that, while not fatal, impede the smooth flow of reading. In Section 2.1, the explanation of the pipeline stages is accurate but suffers from repetitive sentence structures ("First, it... Second, it..."). A more integrated sentence
