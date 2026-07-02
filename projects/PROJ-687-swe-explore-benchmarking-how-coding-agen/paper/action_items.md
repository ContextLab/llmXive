# Automated-review action items — SWE-Explore: Benchmarking How Coding Agents Explore Repositories

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Section 3.2 lists 'GPT-5.4', 'Gemini-3-Pro', and 'Sonnet-4.6' as source models for ground truth. These versions do not exist. Correct to actual existing models (e.g., GPT-4o) to validate the trajectory-grounded claim.
- **[science]** Table 1 claims SWE-Explore is the only benchmark with 'Trajectory-Grounded GT'. ContextBench (li2026contextbench) uses agent trajectories for gold contexts. Verify if this distinction is accurate or if the table entry is incorrect.
- **[writing]** Abstract claims r=0.950 correlation on n=150 instances. Explicitly state the p-value in the text to fully support the statistical significance of the 'strong tracking' claim.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a placeholder error ('to either % of R_core') instead of specifying the actual degradation percentages or fractions corresponding to the x-axis values.
- **[science]** Figure 1: The 'Harder subset' plots (right two) have a y-axis scale (0.0–10.0) that is an order of magnitude smaller than the 'Easier subset' plots (0–60), which may obscure performance differences or make the 'Harder' results appear deceptively flat without explicit visual emphasis.
- **[writing]** Figure 3: The legend in the 'Repository Snapshot' panel uses the term 'core' to label the green file icons, but the caption defines 'core' as a 'span' (line range). This creates ambiguity between file-level and line-level granularity.
- **[writing]** Figure 3: The 'Explorer Output P' table uses the term 'core hit' in the 'GT label' column, but the legend in the 'Repository Snapshot' panel only defines 'core' and 'target', lacking a definition for 'hit'.
- **[fatal]** Figure 6: The caption is explicitly '(no caption)', yet the figure displays specific data (language distribution of 848 instances) that is identical to Figure 4. This renders the figure uninterpretable in isolation and suggests a duplicate file or missing caption error.
- **[science]** Figure 6: The chart displays a total of 848 instances, but the sum of the individual language counts shown (547+84+51+31+30+28+27+22+21+7) equals 848. However, the visual representation of the smallest slices (C++, C, Ruby) is extremely thin and crowded, making it difficult to distinguish them without the leader lines, which is a common issue with donut charts for many categories.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'agentic explorers' and 'agentic localization' upon first use. The term 'agentic' is used as a noun/adjective without definition, assuming reader familiarity with specific agent architectures.
- **[writing]** Define 'trajectory-grounded' and 'trajectory-grounded supervision' at first mention. While context implies it relates to agent execution logs, the specific mechanism of deriving ground truth from trajectories needs a plain-language gloss.
- **[writing]** Replace 'downstream repair behavior' with 'subsequent code-fixing performance' or similar. 'Downstream' is standard in ML but can be opaque to general software engineering readers; 'repair behavior' is slightly jargon-heavy compared to 'fixing bugs'.
- **[writing]** Define 'restricted-context environment' or 'restricted-context validation' clearly. The term implies a specific experimental setup but lacks a brief explanatory clause for non-specialists.
- **[writing]** Clarify 'operating point' in Section 5.2. The phrase 'occupy nearly the same operating point' is technical jargon from systems/ML that should be replaced with 'perform similarly' or 'achieve comparable results' for broader accessibility.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The abstract claims exploration and repair measure the 'same underlying capability' due to high correlation. This conflates correlation with identity. Repair also requires generation; the logic should state exploration is a necessary precursor, not the same capability.
- **[science]** Ground truth requires >=2 successful trajectories, excluding unsolvable or idiosyncratic cases. This limits the benchmark's logical scope to 'consensus-solvable' instances, contradicting claims of general repository exploration evaluation.
- **[writing]** The degradation analysis attributes a performance dip at alpha=25 to 'memorization' without ruling out noise effects. This causal claim is speculative and unsupported by the restricted-context mechanism described.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that 'agentic explorers form a clear tier above classical retrieval' overgeneralizes. Table 2 shows dense retriever 'Potion' fails like random, while only lexical baselines fail. The paper must clarify that the advantage is specific to agentic/interactive methods over lexical search, not all non-agentic methods.
- **[science]** The paper claims to 'isolate' exploration, yet ground truth is derived only from successful repair trajectories. This biases the benchmark toward solvable issues. The authors admit this in the abstract but then claim to measure general 'repository understanding.' Claims should be narrowed to 'exploration for successful repair' to avoid overreach.
- **[writing]** The statement that high correlation (r=0.950) is 'expected' because metrics measure the 'same underlying capability' is an over-interpretation. The correlation is specific to the fixed downstream agent (Mini-SWE-Agent) and budget. The paper should clarify that metrics predict repair only within this specific protocol, not universally.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Dual-Use Considerations' section (Appendix) is currently a single sentence recommending access controls. Given the benchmark's focus on automated code analysis and vulnerability discovery, expand this to explicitly detail the specific risks (e.g., automated vulnerability scanning, supply chain attack generation) and the concrete mitigation strategies implemented (e.g., data sanitization protocols, release restrictions).
- **[writing]** The ground truth derivation relies on trajectories from proprietary models (GPT-5.4, Gemini-3-Pro, etc.). While the data is public, the methodology section should explicitly state whether any PII, secrets, or sensitive configuration data were present in the original trajectories and describe the specific sanitization process used to remove them before benchmark release.
- **[writing]** The selection bias limitation (requiring two successful trajectories) is acknowledged, but the ethics statement should briefly address whether this exclusion of unsolvable/complex issues might inadvertently bias the development of agents toward only 'easy' vulnerabilities, potentially leaving critical, hard-to-find bugs unaddressed by future tools trained on this data.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The correlation analysis in Table 3 (Section 5.2) relies on a subset of n=150 instances. While CIs are now reported, the paper must explicitly justify why this subset is representative of the full 848-instance benchmark to avoid selection bias in the correlation claims.
- **[science]** The ground-truth construction requires at least two successful agent trajectories (Section 3.3). This creates a 'survivorship bias' where the benchmark only evaluates exploration on problems solvable by current SOTA agents. The authors must discuss how this limits the benchmark's utility for evaluating explorers on harder, currently unsolvable issues.
- **[science]** In the degradation analysis (Section 5.4, Fig 3), the claim that 'missing context is the dominant failure mode' relies on a threshold effect observed in the data. The authors should clarify if the statistical significance of the jump between alpha=50 and alpha=75 holds across all tested patchers, or if it is specific to the GPT-5.4-mini/stronger pair.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The abstract and Section 5.2 report a Pearson correlation of r=0.950 on n=150 instances but omit 95% confidence intervals. Please report the CI for both Pearson's r and Spearman's rho in Table 3 to quantify the precision of these estimates.
- **[science]** In Section 5.4 (Degradation Analysis), pairwise comparisons (e.g., alpha=50 vs alpha=75) are mentioned with Holm-Bonferroni correction, but the specific p-values and the exact test statistic (t-statistic) are not reported in the text or tables. Please add these values to ensure reproducibility.
- **[science]** The ground-truth construction relies on the intersection of successful trajectories (Section 3.3). This introduces a selection bias where only solvable instances are included. Please explicitly quantify the size of the excluded set (instances with <2 successful trajectories) and discuss how this limits the generalizability of the 'missing context is dominant' conclusion to unsolvable or hard-to-solve issues.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract, the sentence 'This high correlation is expected: exploration metrics and downstream repair behavior both measure the same underlying capability' reads as a defensive justification rather than a neutral scientific observation. Rephrase to state the finding objectively (e.g., 'This strong correlation suggests that...') to maintain the paper's analytical tone.
- **[writing]** Section 3.2 (Data Sources) contains a grammatical agreement error: 'As Table 1 and Figure 1 summarizes...' should be 'summarize' to agree with the plural subject. Additionally, the phrase 'embedded in repositories that average 759 files' is slightly clunky; consider 'with repositories averaging 759 files' for better flow.
- **[writing]** In Section 5.2, the phrase 'The larger pattern is more important than the exact ordering' is vague. Clarify what 'larger pattern' refers to (e.g., 'The consistent gap between file-level and line-level performance') to ensure the reader immediately grasps the intended takeaway without ambiguity.
