---
action_items:
- id: ddd9e34cc309
  severity: writing
  text: The review focuses strictly on the accuracy of factual claims and the validity
    of their supporting citations. The manuscript makes several strong claims regarding
    the state of the art and the properties of existing benchmarks. In the Introduction,
    the authors state that "ConTextTab set the SOTA for the CARTE benchmark" citing
    [spinaci_contexttab_2025]. A check of the provided bibliography reveals a potential
    mismatch or missing entry for this specific citation key (the .bib file lists
    arazi_tabs
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:46:50.787941Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses strictly on the accuracy of factual claims and the validity of their supporting citations.

The manuscript makes several strong claims regarding the state of the art and the properties of existing benchmarks. In the Introduction, the authors state that "ConTextTab set the SOTA for the CARTE benchmark" citing [spinaci_contexttab_2025]. A check of the provided bibliography reveals a potential mismatch or missing entry for this specific citation key (the .bib file lists `arazi_tabstar_2025` but the text cites `spinaci_contexttab_2025` in multiple places, and the specific SOTA claim on CARTE needs to be explicitly verifiable in the cited work). If the cited paper does not explicitly claim SOTA status on CARTE, this is an unsupported factual assertion.

In Section 3, the selection of embedding models is justified by citing [muennighoff_mteb_2023] for "high performance-to-parameter efficiency." This citation key is missing from the provided `neurips2026.bib` file. While the claim about the models' efficiency might be true, the citation provided does not exist in the bibliography, rendering the support for this specific claim invalid in the current manuscript state.

Furthermore, in Section 5, the text discusses the comparison between "TAR Small" and "Frozen Large" variants. The sentence structure implies that the observation that TAR Small outperforms Frozen Large is a finding of the current study, which is correct. However, the sentence immediately preceding it cites [grinsztajn_vectorizing_2023] regarding the standard practice of PCA. The flow of the paragraph risks conflating the citation of standard practice with the novel empirical finding. The authors should ensure the citation is not misread as supporting the specific "TAR Small > Frozen Large" result, which is a new contribution of this paper.

Finally, the Abstract claims MulTaBench is the "largest image-tabular benchmarking effort to date." This is a superlative claim that requires rigorous verification against all cited benchmarks (MuG, BAG, TIME, etc.). The text mentions MuG has 4 data sources and BAG has 11, but the authors should explicitly confirm that no other un-cited or partially cited benchmark exceeds the 20-image dataset count to ensure the claim is not an overstatement.

These issues are primarily regarding the precision of citations and the verification of superlative claims. They do not invalidate the core science but require correction to ensure factual accuracy and proper attribution.
