---
action_items:
- id: cafadaef3e2d
  severity: science
  text: Theoretical claims (Theorem 1, Sec 3.3) assert strict superiority of active
    over passive retrieval but rely on a synthetic 'Binary-Tree Needle-in-a-Haystack'
    task. The paper lacks empirical evidence that this theoretical separation translates
    to the complex, noisy distributions of LoCoMo/LongMemEval. Re-run experiments
    with a controlled ablation where baselines are given oracle access to the 'correct
    path' to isolate the value of the reconstruction mechanism itself.
- id: 43abc89b272d
  severity: science
  text: Statistical significance is not reported for the main results in Table 1 (LoCoMo)
    or Table 2 (LongMemEval). Given the large performance gaps (e.g., 23% gain), standard
    error bars or p-values from multiple random seeds are required to rule out variance
    or specific seed bias, especially since baselines like Mem0 show high variance
    across categories.
- id: 1902aa7f073a
  severity: science
  text: The cost analysis (Table 2) claims MRAgent reduces token consumption to 118k
    vs 632k for A-Mem. However, the 'Active Reconstruction' process involves iterative
    LLM calls (Algorithm 1, lines 4-10) which typically increase token usage. The
    paper must explicitly detail how the 'on-demand' pruning offsets the overhead
    of multi-step reasoning to achieve this net reduction, or provide a breakdown
    of tokens per step.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:13:17.367933Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architectural shift from passive retrieval to active reconstruction, supported by a clear theoretical framework (Theorem 1, Sec 3.3) and strong empirical gains on LoCoMo and LongMemEval. The ablation studies (Fig 4) effectively isolate the contribution of the reasoning mechanism versus the graph structure. However, the scientific evidence requires strengthening in three areas before the claims can be considered fully robust.

First, the theoretical proof of superiority relies on a "Binary-Tree Needle-in-a-Haystack" task (App. Sec 4.3). While mathematically sound for that specific synthetic distribution, the paper does not demonstrate that this theoretical separation holds under the noisy, semantic distributions of the real-world benchmarks. The large performance gaps (e.g., 23% on Gemini) could potentially be driven by the specific graph topology or the LLM's ability to follow instructions rather than the fundamental "active vs. passive" distinction. An experiment where baselines are augmented with oracle knowledge of the correct retrieval path would help isolate the specific value of the reconstruction logic.

Second, the statistical rigor of the main results is insufficient. Table 1 and Table 2 report single-point estimates for F1 and J scores. Without standard deviations, confidence intervals, or p-values derived from multiple random seeds, it is impossible to determine if the observed improvements are statistically significant or artifacts of a specific evaluation seed. Given the high variance often seen in LLM agent evaluations, this is a critical omission.

Third, the cost analysis presents a counter-intuitive claim: that an iterative, multi-step reasoning process (Algorithm 1) reduces total token consumption compared to baselines. While the "on-demand" pruning is a valid hypothesis, the paper lacks a granular breakdown of token usage per reasoning step versus the savings from not retrieving irrelevant context. The current evidence (Table 2) is a black-box aggregate that does not fully substantiate the mechanism of efficiency.

Finally, the "Evidence Recall" metric is mentioned in the text but not explicitly tabulated with ground-truth definitions in the main results, making it difficult to verify the claim that "multi-hop queries benefit substantially" (Sec 5.5) without relying solely on the final answer accuracy. Providing the raw evidence recall numbers would strengthen the causal link between the reconstruction process and the final performance.
