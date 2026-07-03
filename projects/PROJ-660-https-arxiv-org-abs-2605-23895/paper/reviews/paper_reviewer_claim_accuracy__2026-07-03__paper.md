---
action_items:
- id: 030f20124419
  severity: writing
  text: The claim that 260 concepts were constructed using 'ChatGPT (GPT-5)' (Sec
    3, line 1) is factually unsupported. GPT-5 is not a publicly released model as
    of the paper's context (2025/2026), and the citation 'openai2025gpt5systemcard'
    refers to a system card that likely does not exist or is speculative. Authors
    must clarify the actual model used (e.g., GPT-4o) or remove the specific version
    claim to avoid misrepresentation of the experimental setup.
- id: b35a3950c222
  severity: writing
  text: The claim that 'over 70% [of activation-based localizations] failing to exhibit
    concept-specific responses' (Abstract, line 12; Intro, line 24) is slightly overstated
    based on the provided text. The Results section (Sec 4.1, 'Activation-Based Regions
    Have High False Positive Rate') explicitly states the rate is 'nearly 70%' and
    later specifies '73.4%'. While close, the abstract should align precisely with
    the specific statistic reported in the results to maintain strict factual accuracy.
- id: 8ad1386efe9c
  severity: writing
  text: The citation 'Bao2025MindSimulator' is used to support the claim that MindSimulator
    'retrieves images from COCO using CLIP scores' (Sec 4.1, line 3). However, the
    bibliography entry for Bao2025MindSimulator is an arXiv preprint. Authors should
    verify that the specific implementation details (COCO retrieval, CLIP usage) are
    explicitly described in that preprint and not conflated with other works, as the
    citation does not inherently prove the specific dataset source without the text
    of the paper.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:18:42.449763Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the support provided by citations within the manuscript.

**Factual Accuracy of Model Claims**
A significant factual discrepancy exists in Section 3 ("The BrainCause Framework"), where the authors state: "We automatically constructed a list of 260 concepts using ChatGPT (GPT-5)~\cite{openai2025gpt5systemcard}." As of the current scientific timeline (2025/2026), GPT-5 is not a publicly available or standard model for such tasks, and the citation points to a "System Card" which may be speculative or non-existent in the public domain. If the authors used GPT-4o or another available model, this claim is factually incorrect and misrepresents the experimental reproducibility. If GPT-5 was indeed used in a private beta, the citation must be valid and the claim qualified. This requires immediate correction to ensure the methodology is accurately described.

**Precision of Statistical Claims**
The Abstract and Introduction claim that "over 70%" of activation-based localizations are false positives. The Results section (Section 4.1, paragraph "Activation-Based Regions Have High False Positive Rate") provides a more precise figure: "nearly 70%" and later "73.4%". While the difference is minor, the phrase "over 70%" in the abstract is technically accurate (73.4 > 70), but the phrasing "nearly 70%" in the body creates a slight inconsistency in tone. More importantly, the claim that "over 70% failing... despite achieving high activation scores" is supported by the data, but the authors should ensure the abstract's "over 70%" aligns with the specific "73.4%" figure to avoid any ambiguity about the magnitude of the effect.

**Citation Support for Methodological Details**
The paper cites `Bao2025MindSimulator` to support the description of the MindSimulator baseline method, specifically that it "retrieves images from COCO using CLIP scores" (Section 4.1). While the citation is appropriate for the method's name, the specific claim about the dataset (COCO) and the retrieval mechanism (CLIP) must be explicitly verifiable in the cited preprint. If the preprint describes a different dataset or retrieval method, this attribution is inaccurate. Given that the authors also mention using a "120K unlabeled images from COCO" pool in their own setup (Appendix), there is a risk of conflating the baseline's original setup with the authors' modified setup. The text should clarify if the MindSimulator baseline was re-implemented exactly as described in the paper or if the authors adapted it, ensuring the citation accurately reflects the source of the specific implementation details.

**Conclusion**
The core scientific claims regarding the superiority of causal discovery over activation-based methods are supported by the presented data (Tables 1, 2, 3). However, the specific claim regarding the use of "GPT-5" is a factual error that must be corrected. Additionally, minor clarifications on the precision of the false positive rate and the exact implementation details of the baseline method are recommended to ensure strict adherence to factual accuracy.
