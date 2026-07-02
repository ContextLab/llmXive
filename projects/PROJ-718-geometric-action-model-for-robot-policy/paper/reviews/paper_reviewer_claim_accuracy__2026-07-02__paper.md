---
action_items:
- id: b0c52cf46a99
  severity: writing
  text: The '55x faster' claim (Abstract, Intro) compares GAM with CUDA Graphs (6.9ms)
    against baselines without it. Clarify that this speedup includes deployment optimizations
    not applied to baselines, or re-evaluate baselines with the same settings for
    a fair architectural comparison.
- id: 3231216385c5
  severity: writing
  text: The '9.7%p' camera perturbation gain (Intro) compares GAM to Cosmos-Policy
    (73.4%) but ignores $\pi_{0.5}$ (72.0%). Specify that the gain is relative to
    the best WAM baseline or clarify the comparison scope to avoid implying a universal
    lead over all foundation models.
- id: e4c46b54c158
  severity: writing
  text: The '784K trajectories' claim (Sec 4.1) lacks explicit confirmation in the
    appendix. State the exact filtered dataset count or link the 784K figure to the
    specific OXE/MimicGen/RoboCasa365 split to ensure reproducibility of the data
    scale.
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:57:36.739629Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their support by the provided evidence and citations.

**1. Inference Speed Claim (55x Faster):**
The paper repeatedly claims GAM is "55$\times$ faster" than baselines (Abstract, Introduction, Section 4.2). The Appendix (Table D.1) reveals a methodological inconsistency in this comparison. GAM's 6.9ms latency is achieved using **CUDA Graphs**, whereas the baseline latencies (e.g., $\pi_{0.5}$ at 29.2ms, Cosmos Policy at 382.4ms) are reported **without** CUDA Graphs (indicated by the $\times$ in the "CUDA Graphs" column). While the authors note in the appendix that GAM's deployment setting uses this optimization, the main text presents the 55x figure as a general architectural advantage over "diffusion-based Cosmos Policy" without qualifying that the baseline was not optimized with the same deployment technique. A fair comparison would either apply CUDA Graphs to the baselines (if supported) or explicitly state that the speedup is relative to the specific unoptimized baseline configurations. The current phrasing overstates the architectural speed advantage by conflating it with deployment-specific optimizations.

**2. Camera Perturbation Performance Claim:**
The Introduction claims GAM achieves "outstanding performance in camera perturbation settings ($\uparrow$9.7\%p)." Table 1 (LIBERO-Plus) shows GAM at 83.1% success rate in the "Cam." column. The closest WAM baseline, Cosmos-Policy, is at 73.4%, yielding a 9.7% point gap. However, the VLA baseline $\pi_{0.5}$ is at 72.0%. The claim is technically accurate regarding the gap to the *best* baseline (Cosmos), but the phrasing "outstanding performance... which requires geometric understanding priors" implies a universal superiority over all foundation models. The gap to the best VLA ($\pi_{0.5}$) is 11.1%, which is larger, but the text does not distinguish between the types of baselines in this specific claim. While not a factual error, the claim would be more precise if it specified "outperforming the best video-based world model baseline by 9.7%."

**3. Dataset Scale Claim:**
The Introduction and Section 4.1 state the model is pretrained on "784K single-arm robot trajectories." The Appendix (Section A.1) details the data sources (OXE, MimicGen, RoboCasa365) and their ratios (72%, 18%, 10%) but does not explicitly confirm the total count of 784K. While this number is likely the result of the authors' filtering process, the claim is a specific factual assertion that should be explicitly tied to the filtered dataset count in the text or appendix to ensure the reader can verify the scale of the training data.

**4. Citation Support:**
The citations for baseline methods (e.g., $\pi_{0.5}$, Cosmos-Policy, OpenVLA) are generally accurate and correspond to the correct arXiv preprints or papers listed in the bibliography. The claim that "3D cues... are left implicit" in VLAs is supported by the cited literature (e.g., \cite{fei2025libero} which analyzes VLA robustness). The claim that GFMs are used as "static feature extractors" in prior work is supported by the cited papers (e.g., \cite{li2025spatial}, \cite{sun2026rocket}). No unsupported citations were found.

**Conclusion:**
The paper's core scientific claims are supported by the data, but the specific quantitative claims regarding inference speed and the precise nature of the performance gap in camera perturbations require minor clarification to avoid overstatement or ambiguity regarding the comparison conditions.
