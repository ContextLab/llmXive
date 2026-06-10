---
action_items:
- id: 22b62de9ca9c
  severity: science
  text: "Clarify the scope of the randomized\u2011direction oracle\u2019s unbiasedness.\
    \ The proof (Appendix\u202FA) assumes strict pair\u2011consistency, which may\
    \ be violated by real LLM APIs (hidden state, non\u2011stationarity). Either provide\
    \ empirical validation of the unbiasedness claim or temper the statement to reflect\
    \ this assumption."
- id: 6ffb4d4b3f72
  severity: writing
  text: "Revise the \u201Cdrop\u2011in replacement\u201D claim (Abstract & Conclusion).\
    \ Active rankers require a warm\u2011up phase (\u2248K\xB2 calls) and hyper\u2011\
    parameters (e.g., the PAC pool multiplier\u202Fm). Explicitly discuss these prerequisites\
    \ and their impact on deployment complexity."
- id: 1199d7d238b6
  severity: science
  text: "Limit the prescriptive recipe (\u201Cuse Mohajer with randomized\u2011direction\
    \ when budget exceeds the warm\u2011up threshold\u201D) to the specific models\
    \ and datasets evaluated (Flan\u2011T5\u2011L/XL, Qwen\u20113\u20114B). Acknowledge\
    \ that performance may differ for other LLM families or larger candidate pools."
- id: acf2c4490884
  severity: writing
  text: "Add a discussion of how the reported latency estimates (Section\u202F6) might\
    \ change with realistic parallel batching, and qualify any conclusions about \u201C\
    time\u2011to\u2011quality\u201D that are based on sequential upper\u2011bounds."
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T16:27:40.144939Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents an appealing reframing of Pairwise Ranking Prompting (PRP) as an active‑learning problem and demonstrates empirical gains on several benchmark collections. However, several statements extend beyond what the presented data and methodology can substantiate.

First, the claim that the randomized‑direction oracle “converts systematic position bias into zero‑mean noise, enabling unbiased aggregate ranking” rests on a theoretical proof that assumes strict pair‑consistency (Appendix A). Real‑world LLM APIs exhibit hidden state, caching, and non‑stationary behavior that can break this assumption, yet the paper does not provide empirical evidence that the unbiasedness holds in practice. This overreach should be either experimentally validated (e.g., by measuring residual bias across multiple seeds) or the claim should be qualified.

Second, the authors describe active rankers as “drop‑in replacements” for sorting‑based PRP rerankers. While the active methods indeed require no model training, they depend on a warm‑up budget (≈K × K calls) before they become effective and on hyper‑parameters such as the PAC pool multiplier m. These practical requirements are not highlighted in the abstract or conclusion, giving the impression that the methods can be swapped in without adjustment. Explicitly stating these prerequisites would align the claim with the experimental setup.

Third, the paper offers a general recipe for practitioners: use Mohajer with the randomized oracle when the call budget exceeds the warm‑up threshold, otherwise fall back to sorting. This recommendation is derived from experiments with Flan‑T5‑L/XL and Qwen‑3‑4B on TREC‑DL and BEIR tasks. It is therefore premature to present it as universally applicable; performance may vary with other LLM families, larger candidate sets, or different retrieval domains. The authors should restrict the prescription to the evaluated settings or provide additional evidence of broader applicability.

Finally, latency analyses (Section 6) rely on a sequential upper‑bound that ignores parallel batching, which the authors acknowledge but still draw strong conclusions about “time‑to‑quality.” Since parallel execution can substantially alter wall‑clock times, the discussion should be tempered to reflect this limitation.

Addressing these points will tighten the alignment between claims and evidence, improving the paper’s scientific rigor without altering its core contributions.
