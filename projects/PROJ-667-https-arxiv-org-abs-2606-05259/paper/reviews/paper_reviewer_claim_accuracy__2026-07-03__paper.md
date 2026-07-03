---
action_items:
- id: 91fa71183668
  severity: science
  text: The Introduction claims the benchmark is filtered so that 'single-frame probing
    fails for all three frontier models (Claude-4.5-Sonnet, Qwen3-VL-235B-A22B, GPT-5.2).'
    These model names (e.g., 'GPT-5.2', 'Claude-4.5') appear to be hallucinated or
    future-dated, as no such public models exist as of the paper's context. This undermines
    the factual accuracy of the benchmark's difficulty claim.
- id: d50ebc247825
  severity: writing
  text: Table 1 and the Abstract state the corpus contains '145K newly collected CC-licensed
    videos' and '315K examples.' However, the 'Domain Knowledge Bank' subsection claims
    'numknow = 63,745 knowledge points.' The relationship between 63k knowledge points
    and 145k videos (avg ~2.3 videos per point) is not explained, nor is the derivation
    of 315k QA pairs from these points clear. The claim of 'expert-validated selection'
    needs specific citation or methodology to support the scale.
- id: e3b476466c68
  severity: fatal
  text: The paper cites 'GPT-5.2' and 'Claude-4.5-Sonnet' in the Introduction and
    Table 2 as baselines. These models do not exist in the public domain or the provided
    bibliography. Citing non-existent models as state-of-the-art baselines is a critical
    factual error that invalidates the comparative performance claims.
artifact_hash: 442b60f42997ea4620ca51b6cec07f843dd48ca52b119472ba764f9d3b1bfbac
artifact_path: projects/PROJ-667-https-arxiv-org-abs-2606-05259/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:01:50.695891Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses strictly on the factual accuracy of claims and the validity of their supporting citations.

**Critical Factual Errors in Model Citations:**
The most severe issue lies in the Introduction (Section 1) and Table 2, where the authors claim their benchmark (\eval) was filtered to ensure "single-frame probing fails for all three frontier models (Claude-4.5-Sonnet, Qwen3-VL-235B-A22B, GPT-5.2)." The model names "GPT-5.2" and "Claude-4.5-Sonnet" are factually incorrect; as of the current date, OpenAI has not released a GPT-5 series, and "Claude-4.5" is not a known release. Similarly, "Qwen3-VL-235B-A22B" appears to be a hallucinated or non-standard version string not found in the provided bibliography or public records. Citing non-existent models as the baseline for filtering a benchmark renders the claim of the benchmark's difficulty unsupported and scientifically invalid.

**Inconsistency in Data Statistics:**
In Section 3.1 ("Domain Knowledge Bank"), the text states: "We assembled \numknow knowledge points (\numknowuse used) across 82 subjects... (\numknow = 63,745 knowledge points, \nexample = 315,537 QA pairs)." The LaTeX source uses macros (`\numknow`) that are not defined in the provided snippet, but the text explicitly fills in "63,745". The Abstract and Table 1 claim "145K videos" and "315K examples." While the math (315k examples / 63k points ≈ 5 examples per point) is plausible, the claim that these are "newly collected" and "CC-licensed" for *every* video requires verification. The paper states "All videos are newly collected and CC licensed" (Abstract, Fig 1 caption), but the methodology for ensuring 145K *unique* CC-licensed videos across 82 professional subjects without overlap or copyright issues is not detailed with sufficient evidence to support the "100% CC" claim in Table 1.

**Benchmark Filtering Claim:**
The claim that the benchmark is "filtered to require genuine video reasoning" because single-frame probing fails for the cited (non-existent) models is circular and factually unsound. If the baseline models do not exist, the filtering criterion cannot be verified. The authors must replace these citations with actual, existing models (e.g., GPT-4o, Claude 3.5 Sonnet, Qwen2.5-VL) and re-verify the filtering statistics.

**Conclusion:**
The paper makes central claims about its benchmark's difficulty and the state-of-the-art baselines using hallucinated model names. This is a fatal factual error regarding the accuracy of the claims. The data statistics also lack clear derivation from the knowledge points to the final example count, requiring clarification.
