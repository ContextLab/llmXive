---
action_items:
- id: b177c8ffba0d
  severity: science
  text: The abstract claims the framework introduces 'Smoothed Sensitivity Transformation
    (SST) for noise handling,' yet SST is never defined, referenced, or utilized in
    the methodology (Sec 3) or experiments. This appears to be an unsupported claim
    of novelty or a hallucinated component. Remove the reference to SST or explicitly
    describe its implementation and results.
- id: ee4fc83c4725
  severity: writing
  text: "The abstract states that the randomized-direction oracle enables 'unbiased\
    \ aggregate ranking... assuming strict pair-consistency.' However, the proof in\
    \ Appendix (Sec:unbiased-proof) only demonstrates reciprocity in expectation ($\P\
    r[V_{ij}=1] = 1 - \Pr[V_{ji}=1]$), not that the resulting ranking is unbiased\
    \ relative to the true relevance. The claim of 'unbiased aggregate ranking' overreaches\
    \ the mathematical guarantee provided."
- id: 89a02abdcb51
  severity: writing
  text: The Introduction claims active rankers reach NDCG@10 comparable to QuickSort
    with 'up to 7x fewer calls.' While Table 2 shows significant call reductions,
    the specific '7x' figure is not explicitly calculated or cited for a specific
    dataset/budget pair in the text, making the magnitude of the claim difficult to
    verify without manual calculation. Clarify the specific instance where this ratio
    is achieved.
artifact_hash: 8b4e5d074a64eaa78e7927259e08b3cc001daf353c2dc417958eda25d90e918a
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:11:28.960327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper generally avoids over-claiming regarding the superiority of active learning over sorting, carefully delineating the "warm-up" phase where sorting is preferable (Section 5, "Bidirectional oracle"). The limitations section is robust, explicitly acknowledging the lack of theoretical explanation for the randomized-direction oracle's gains and the potential for API non-stationarity.

However, there are specific instances of overreach and unsupported claims:

1.  **Hallucinated/Undefined Methodology (Abstract):** The abstract lists "Smoothed Sensitivity Transformation (SST) for noise handling" as a key component of the framework. A thorough scan of the methodology (Section 3), results, and appendix reveals no definition, algorithm, or experimental application of SST. This is a significant over-claim of novelty and methodological scope. If SST was not used, it must be removed from the abstract. If it was used, it must be detailed in the body.

2.  **Overstated Theoretical Guarantees (Abstract & Appendix):** The abstract claims the randomized-direction oracle enables "unbiased aggregate ranking." The proof provided in the Appendix (Section:unbiased-proof) only establishes that the oracle is *reciprocal in expectation* (i.e., $P(A>B) = 1 - P(B>A)$). It does not prove that the resulting ranking is unbiased with respect to the ground truth relevance, nor does it account for the bias introduced by the specific active learning selection strategy. The claim of "unbiased aggregate ranking" is stronger than the mathematical evidence provided.

3.  **Unsubstantiated Magnitude (Introduction):** The claim that active rankers use "up to 7x fewer calls" than QuickSort is a specific quantitative assertion. While Table 2 supports a reduction, the text does not explicitly point to the specific dataset and budget where this 7x factor is realized. While likely true based on the data (e.g., QuickSort ~1669 calls vs. Mohajer ~232 calls in Table 2), the lack of a direct citation to the specific data point makes the claim feel slightly exaggerated without immediate verification.

The paper is otherwise careful in its claims, particularly regarding the trade-offs between budget and performance. The primary issue is the inclusion of an undefined method (SST) and the slight inflation of the theoretical guarantee regarding unbiasedness.
