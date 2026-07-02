---
action_items:
- id: 27858c7e309d
  severity: writing
  text: The paper addresses safety and ethics primarily through a dedicated "Potential
    Negative Societal Impact" section in the Appendix. While the authors correctly
    identify risks such as the generation of sexually explicit content, reinforcement
    of stereotypes, and the creation of misleading advertisements (Appendix, "Potential
    Negative Societal Impact"), the discussion remains high-level. The manuscript
    lists these risks but fails to propose specific, actionable mitigation strategies
    or technical saf
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:11:00.820114Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper addresses safety and ethics primarily through a dedicated "Potential Negative Societal Impact" section in the Appendix. While the authors correctly identify risks such as the generation of sexually explicit content, reinforcement of stereotypes, and the creation of misleading advertisements (Appendix, "Potential Negative Societal Impact"), the discussion remains high-level. The manuscript lists these risks but fails to propose specific, actionable mitigation strategies or technical safeguards (e.g., integrated watermarking, content filtering mechanisms, or strict usage policies) that would accompany the release of the model or code. Given the application's focus on human-centric video customization, which is highly susceptible to deepfake misuse, a more robust discussion on deployment safety is required.

Regarding data provenance, the "High-Quality Data Curation Pipeline" (Appendix, Sec. 1) describes collecting "a large set of raw videos from the Internet" and filtering them. The paper does not specify the source of these videos (e.g., specific platforms, public datasets) nor does it address the legal and ethical implications of scraping and using this data for training, particularly concerning copyright and the consent of individuals depicted in the videos. The use of VLMs (Gemini-3.1) to generate captions and verify garments further introduces potential biases from the underlying models, which should be acknowledged.

Additionally, the construction of the HGC-Bench (Appendix, Sec. HGC-Bench Details) states that the authors "anonymize identifiable facial information via face swapping." It is unclear whether this anonymization was applied to the reference images used for evaluation or if it refers to a privacy-preserving step in the dataset creation. If the reference images were anonymized, the validity of the "ID Consistency" (Cur Score) metric, which relies on facial embeddings (ArcFace), is compromised. The authors must clarify the exact nature of this anonymization and its impact on the evaluation metrics.
