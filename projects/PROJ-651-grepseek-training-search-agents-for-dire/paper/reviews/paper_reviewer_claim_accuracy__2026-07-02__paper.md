---
action_items:
- id: 649f8e734d4f
  severity: writing
  text: 'The paper makes several specific factual claims regarding dataset composition,
    performance metrics, and statistical significance that require tighter alignment
    with their cited sources or internal consistency. First, the description of the
    corpus in Section 3 ("Experimental Setup") and the Introduction states: "Corpus:
    2018 Wikipedia (21M docs, 14GB)." This claim is attributed to \citep{karpukhin2020dense}.
    However, the Karpukhin et al. (2020) paper (DPR) describes a corpus of 21M *passages*
    ext'
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:07:37.661674Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several specific factual claims regarding dataset composition, performance metrics, and statistical significance that require tighter alignment with their cited sources or internal consistency.

First, the description of the corpus in Section 3 ("Experimental Setup") and the Introduction states: "Corpus: 2018 Wikipedia (21M docs, 14GB)." This claim is attributed to \citep{karpukhin2020dense}. However, the Karpukhin et al. (2020) paper (DPR) describes a corpus of 21M *passages* extracted from Wikipedia, not 21M *documents*. Furthermore, the 14GB figure likely refers to the raw text size of the dump, whereas the DPR corpus is often processed and tokenized. Citing the DPR paper for the specific claim of "21M docs" and "14GB" is slightly inaccurate; the authors should clarify if they are using the raw 2018 dump or the DPR passage set and cite the appropriate source for the file size and document count statistics.

Second, there is a potential ambiguity in the latency claims. The Introduction states the sharded engine reduces latency from 5.39s to 0.71s, "bringing end-to-end latency to ≈ 8.6 seconds per query." The 0.71s figure clearly refers to the retrieval component. The jump to 8.6s implies the LLM generation and tool orchestration take approximately 7.9s. While this is plausible, the phrasing could be misinterpreted as the retrieval engine taking 8.6s. The text should explicitly clarify that the 8.6s is the *total* end-to-end time (retrieval + generation) to ensure the claim accurately reflects the contribution of the proposed engine versus the LLM.

Finally, the paper frequently marks results as statistically significant ($^\uparrow$) in Tables 1 and 2. The Appendix (Table 3 caption) mentions "McNemar’s test, p<0.05" for the EM results. However, the main text and Table 1 (F1 results) do not explicitly specify the statistical test used for the F1 significance claims. To support the "significant" claims rigorously, the authors should confirm that the same statistical test (or an appropriate one for F1 scores) was applied to the F1 results and report this consistently in the main text or table captions.
