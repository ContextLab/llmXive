---
action_items:
- id: 380ed4d12133
  severity: writing
  text: The paper presents a compelling benchmark and a strong central finding regarding
    data mixing, but the evidentiary design for the headline quantitative claims requires
    strengthening to rule out noise and confounds. First, the primary claim of a +5.4pp
    improvement over FineVision (Abstract, Table 1) rests on single-point estimates
    without any measure of variance. In large-scale VLM training, performance can
    fluctuate significantly across random seeds (often >1-2pp). Without reporting
    results acros
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:29:31.264798Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling benchmark and a strong central finding regarding data mixing, but the evidentiary design for the headline quantitative claims requires strengthening to rule out noise and confounds.

First, the primary claim of a +5.4pp improvement over FineVision (Abstract, Table 1) rests on single-point estimates without any measure of variance. In large-scale VLM training, performance can fluctuate significantly across random seeds (often >1-2pp). Without reporting results across at least 3-5 seeds with standard deviations or confidence intervals, it is impossible to determine if this gap represents a robust effect of the proposed data mixture or simply a lucky initialization. The current presentation treats a single run as a generalizable fact, which is insufficient for a benchmark paper.

Second, the conclusion that "filtering rarely helps" (Section 4.2) is potentially confounded by the experimental design. The filtering experiments remove data, thereby changing the total token count and the specific distribution of remaining samples compared to the "No Filter" baseline. A performance drop (or lack of gain) could be due to the reduction in data volume or the specific removal of certain samples, rather than the act of filtering itself. To isolate the mechanism, the authors should include a control experiment where the unfiltered pool is subsampled to match the exact token count and distribution of the filtered pool, ensuring the comparison is strictly about the *quality* of the selected data, not the quantity.

Finally, the attribution of gains to "instruction-heavy mixtures" (Section 5) is complicated by potential compute mismatches. If the baseline models (e.g., FineVision) were trained on different token budgets or with different scaling laws than the DCVLM models, the observed improvement could be driven by the increased scale of the DCVLM training rather than the mixture strategy. The paper needs to explicitly demonstrate that the gains hold when comparing mixtures at identical compute budgets (token counts) to rule out scale as the primary driver.

Addressing these design gaps—specifically by adding seed variance, a compute-matched subsampling control, and explicit token-budget ablations—would solidify the causal claims regarding data mixing and filtering.
