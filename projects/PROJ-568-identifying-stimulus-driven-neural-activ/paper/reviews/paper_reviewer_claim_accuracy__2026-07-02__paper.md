---
action_items:
- id: 57ea60d593c6
  severity: writing
  text: 'Section 1.2.1: The claim that the cortex is 80% mass but 20% neurons cites
    Herc09. Verify if this specific ratio is explicitly in that paper or if it is
    a derived statistic requiring clarification.'
- id: 54b220fa7205
  severity: writing
  text: 'Section 1.2.1: The text cites AzevEtal09 for ''100 billion glial cells,''
    but that paper argues for a ~1:1 ratio (~86B each). The ''100B'' figure contradicts
    the cited source''s main finding. Clarify the numbers.'
- id: 977ee3187554
  severity: writing
  text: 'Section 1.2.1: Claiming single-neuron responses ''can only be measured using...
    iEEG and ECoG'' is inaccurate. Microelectrode arrays (e.g., Utah arrays) also
    measure single units invasively but are distinct from standard iEEG/ECoG.'
- id: fc6c1d5ba2d8
  severity: writing
  text: 'Section 2.1.2: The RSA description implies Pearson correlation is the standard
    method. However, KrieEtal08b emphasizes Spearman/Kendall as robust alternatives.
    Acknowledge this flexibility to align with the source.'
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:24:00.844320Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript provides a comprehensive survey of methods for identifying stimulus-driven neural activity. Most claims are well-supported, but a few specific factual assertions regarding numerical statistics and methodological definitions require verification against the cited sources to ensure strict accuracy.

In Section 1.2.1, the text states the cerebral cortex comprises "roughly 80% of the adult human brain's mass, but only roughly 20% of its neurons," citing Herculano-Houzel (2009). While this paper is the seminal work on total neuron counts (~86 billion) and isometric scaling, the specific 80/20 mass-to-neuron ratio is a derived statistic not explicitly highlighted as a primary finding. The authors should verify if this specific percentage is directly stated in the source or if it requires a qualifier.

Similarly, in the same section, the text claims the brain contains "roughly 100 billion glial cells," citing Azevedo et al. (2009). This paper famously refutes the old "10:1" glia-to-neuron ratio, proposing instead a near 1:1 ratio (approx. 86 billion of each). Citing this work to support a "100 billion" figure for glia creates a numerical inconsistency with the source's primary conclusion. The authors should clarify the specific counts supported by these references.

Additionally, Section 1.2.1 claims that "Stimulus-driven responses in individual neurons... can only be measured using invasive approaches like iEEG and ECoG." This is an overstatement. While iEEG and ECoG are invasive, true single-unit recordings in humans often utilize microelectrode arrays (e.g., Utah arrays) or depth electrodes with micro-wires, which are distinct from standard clinical iEEG/ECoG grids. The text conflates specific modalities with the broader category of invasive single-unit recording.

Finally, in Section 2.1.2, the description of Representational Similarity Analysis (RSA) specifies computing the "element-wise correlation" (implying Pearson) between matrix upper triangles. While common, the foundational paper by Kriegeskorte et al. (2008) explicitly discusses Spearman rank correlation and Kendall's tau as robust alternatives. Presenting Pearson as the singular method without acknowledging the flexibility emphasized in the source text is a minor over-simplification.

Addressing these points will ensure the manuscript's claims align precisely with the evidence provided in the citations.
