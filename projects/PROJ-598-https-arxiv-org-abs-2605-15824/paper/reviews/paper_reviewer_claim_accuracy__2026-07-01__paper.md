---
action_items:
- id: ba9849906c22
  severity: writing
  text: $23.8 / 0.77 \approx 31x$ While the calculated range (31x to 183x) roughly
    aligns with the "30-180x" claim, the upper bound is slightly exceeded. More importantly,
    the claim relies on the specific baselines listed. If the "180x" figure was derived
    from a baseline not included in Table 1 (e.g., a slower configuration or a different
    resolution), the claim is misleading without context. The authors should ensure
    the range strictly reflects the data presented in Table 1 or explicitly state
    which bas
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:09:58.345898Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of their supporting citations.

**Citation Mismatch in Methodology:**
In the Appendix under "1. General Coarse-to-Fine Video Filtering," the authors state: "we estimate optical flow using UniMatch~\cite{li2025unimatch}." However, the corresponding entry in `reference.bib` for `li2025unimatch` is titled "Universal matching from atom to task for few-shot drug discovery." This citation clearly does not support the claim of using UniMatch for optical flow estimation in video processing. This is a significant factual error where the cited source describes a completely different domain (drug discovery) than the claimed application (computer vision/optical flow). The authors must correct this citation to point to the actual optical flow implementation used (likely the correct UniMatch paper by Li et al. in CVPR/ICCV, if different from the drug discovery one, or a different method entirely).

**Verification of Speedup Claims:**
The Abstract and Introduction claim the method is "30-180$\times$ faster than existing baselines." Table 1 (`tab:main_results`) lists baselines with FPS ranging from 0.13 (Kaleido) to 0.77 (Phantom 1.3B). The proposed method achieves 23.8 FPS.
- $23.8 / 0.13 \approx 183x$
- $23.8 / 0.77 \approx 31x$
While the calculated range (31x to 183x) roughly aligns with the "30-180x" claim, the upper bound is slightly exceeded. More importantly, the claim relies on the specific baselines listed. If the "180x" figure was derived from a baseline not included in Table 1 (e.g., a slower configuration or a different resolution), the claim is misleading without context. The authors should ensure the range strictly reflects the data presented in Table 1 or explicitly state which baselines define the bounds.

**Future-Dated Citations:**
The bibliography includes entries with future publication years, such as `wang2026customvideo` (TMM, 2026) and `xue2025stand` (CVPR, 2026). While arXiv preprints often have future conference dates, the claim that these works "extend S2V customization" relies on the content of these papers. If these papers are not yet publicly available or if the "2026" date is a placeholder for a submission that hasn't been accepted, the claim cannot be independently verified by the reader. The authors should ensure these references are valid, accessible preprints or clearly marked as "in press" if the acceptance is confirmed.

**Conclusion:**
The paper makes strong claims about performance and methodology that are currently undermined by a clear citation error (drug discovery vs. optical flow) and potentially ambiguous speedup calculations. Correcting the `li2025unimatch` citation is critical for the scientific integrity of the data curation pipeline description.
