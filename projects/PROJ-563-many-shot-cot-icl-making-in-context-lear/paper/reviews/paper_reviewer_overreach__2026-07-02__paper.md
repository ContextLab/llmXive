---
action_items:
- id: 059b7dad21d1
  severity: writing
  text: The claim that CDS yields 'up to a 5.42 percentage-point gain' (Abstract)
    is not supported by Table 1 in section/curvature.tex, where the maximum observed
    gain is 5.64 (geometry, gpt-5.2, 16 shots). The text must be corrected to reflect
    the actual maximum or the specific condition under which 5.42 was achieved.
- id: 261de02716d0
  severity: writing
  text: The paper claims CDS is a 'simple ordering method' (Abstract) and 'inexpensive'
    (section/curvature.tex), yet the TSP-based heuristic with 2-opt local search on
    a complete graph of 128 nodes is computationally non-trivial for real-time inference.
    The authors should clarify the computational cost or temper claims of 'simplicity'
    to avoid over-selling the method's deployability.
- id: 108746f357e6
  severity: writing
  text: The conclusion states CDS 'yields consistent gains across math and narrative
    reasoning,' but Table 1 shows mixed results for Qwen3 on DetectiveQA (e.g., 75.32
    vs 72.73 is a gain, but 76.62 vs 75.97 is marginal). The term 'consistent' is
    an over-claim given the variance in the data; 'generally' or 'often' would be
    more accurate.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:14:26.067796Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that slightly overreach the provided evidence, primarily regarding the magnitude and consistency of the proposed method's (CDS) performance and the computational simplicity of the approach.

First, the Abstract states that CDS "yields up to a 5.42 percentage-point gain on geometry with 64 demonstrations." However, inspection of Table 1 in `section/curvature.tex` reveals that the maximum gain for geometry is actually 5.64 percentage points (gpt-5.2, 16 shots: 81.21 vs 75.99). The specific value of 5.42 does not appear as a maximum in the table for the 64-shot setting (where the max gain is 5.65 for gpt-5.2). This discrepancy suggests a potential error in the reported statistic or a lack of transparency about which specific configuration yielded the "up to" figure. The claim should be corrected to match the data or explicitly qualified.

Second, the paper characterizes CDS as a "simple ordering method" and notes it is "inexpensive, taking under one minute on a standard CPU for n≤128" (`section/curvature.tex`). While this may be true for offline preparation, describing a TSP-based heuristic with 2-opt local search on a complete graph as "simple" and "inexpensive" in the context of "in-context test-time learning" risks over-selling the method's practicality for dynamic, real-time inference scenarios where low latency is critical. The authors should temper the language regarding simplicity or explicitly distinguish between offline preparation costs and online inference costs to avoid misleading readers about the method's deployment overhead.

Finally, the Conclusion asserts that CDS "yields consistent gains across math and narrative reasoning." While the gains are generally positive, the term "consistent" is too strong given the data in Table 1. For instance, on the DetectiveQA task with Qwen3, the gains are marginal (e.g., 76.62 vs 75.97 at 16 shots) and sometimes non-existent or negative depending on the embedding model used (e.g., CDS_bge vs CDS). A more nuanced phrasing, such as "yields generally positive gains" or "often improves performance," would better align with the observed variance in the results.
