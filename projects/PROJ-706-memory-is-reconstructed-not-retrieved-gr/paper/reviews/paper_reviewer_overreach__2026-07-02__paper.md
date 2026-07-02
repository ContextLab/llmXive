---
action_items:
- id: 836808f94482
  severity: writing
  text: The claim that MRAgent reduces 'runtime costs' is over-claimed. Table 2 shows
    MRAgent (586s) is slower than Mem0 (533s). The text implies universal reduction,
    but data only supports reduction vs. specific graph baselines like A-Mem. Clarify
    this limitation.
- id: 1cfb1a66e763
  severity: science
  text: Theorem 1 claims active retrieval is 'strictly more powerful' based on a binary-tree
    separation task. The paper does not prove LoCoMo/LongMemEval queries match this
    worst-case structure. Attributing empirical gains directly to this theorem risks
    over-extrapolating the theoretical result to the specific dataset.
- id: 06b01e1ca180
  severity: science
  text: Table 2 claims 118k tokens includes 'construction and retrieval.' Given MRAgent's
    multi-step active reconstruction (Algorithm 1), this count seems low. Clarify
    if construction costs are amortized or excluded, as the 'on-demand' efficiency
    claim may be misleading if baselines are compared differently.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:12:38.573638Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the superiority of "active reconstruction" over "passive retrieval" that require tighter alignment with the presented evidence.

First, the claim of reduced computational cost (Abstract; Section 5.1) is potentially over-claimed. Table 2 reports MRAgent at 118k tokens and 586s runtime, compared to Mem0 at 245k tokens and 533s. While MRAgent beats A-Mem and LangMem significantly, it is actually *slower* than Mem0. The text states MRAgent reduces "token and runtime costs" generally, which is inaccurate given the Mem0 comparison. The "on-demand" argument is valid against heavy graph expansion, but the absolute claim of reduced runtime is not supported across all baselines.

Second, the theoretical justification in Section 3.3 (Theorem 1) asserts that active retrieval is "strictly more powerful" based on a constructed binary-tree "needle-in-a-haystack" task. The paper then attributes the empirical performance gains on LoCoMo and LongMemEval directly to this theoretical advantage. However, the paper does not demonstrate that the specific queries in these benchmarks actually exhibit the "needle-in-a-haystack" structure where passive retrieval fails due to combinatorial explosion. If the benchmarks rely more on semantic similarity or simple temporal ordering, the theoretical separation may not be the primary driver of the observed 23% gain. The link between the abstract theorem and the specific dataset characteristics is assumed rather than proven, risking an over-extrapolation of the theoretical result.

Finally, the token count in Table 2 is described as including "memory construction and retrieval." Given that MRAgent performs multi-step active reconstruction (Algorithm 1), which involves iterative LLM reasoning calls, the low token count (118k) is surprising compared to baselines that might use simpler retrieval. If the 118k figure excludes the cost of the initial graph construction (which is likely heavy for the "distillation" phase described in Section 2.3), the comparison is apples-to-oranges. If it includes construction, the efficiency claim is strong but needs explicit confirmation that the construction cost is not being amortized over a different number of queries than the baselines.
