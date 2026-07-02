---
action_items:
- id: 0bfb456c09aa
  severity: writing
  text: The 'Potential Negative Societal Impact' section (Appendix) acknowledges risks
    like deepfakes and bias but lacks concrete mitigation strategies. Explicitly detail
    technical safeguards (e.g., watermarking, NSFW filters) or usage policies intended
    to prevent malicious deployment.
- id: 6f1c224bdfe9
  severity: writing
  text: The data curation pipeline (Appendix, Sec. 1) involves scraping 'raw videos
    from the Internet' and using VLMs for captioning. The manuscript must clarify
    the legal basis for this data collection, confirm adherence to copyright/privacy
    laws, and state whether IRB approval or informed consent was obtained for any
    human subjects in the training data.
- id: 12054869ebc8
  severity: writing
  text: The HGC-Bench construction (Appendix, Sec. HGC-Bench Details) mentions 'anonymize
    identifiable facial information via face swapping.' This process requires rigorous
    verification to ensure re-identification is impossible. The authors should provide
    evidence of the anonymization efficacy or a statement on residual privacy risks.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:00:22.458822Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The manuscript addresses significant safety and ethical considerations regarding human-centric video generation, particularly in the "Potential Negative Societal Impact" section (Appendix) and the data curation pipeline description. The authors correctly identify risks such as the generation of sexually explicit content, the amplification of stereotypes, and the creation of misleading advertisements (Appendix, "Potential Negative Societal Impact"). However, the discussion remains high-level and lacks specific, actionable mitigation strategies. For a technology capable of real-time, interactive garment swapping, the potential for misuse in creating non-consensual deepfakes or fraudulent e-commerce content is non-trivial. The authors should expand this section to include concrete technical safeguards (e.g., integrated watermarking, content moderation filters) or proposed usage policies that would accompany the release of the model or code.

Regarding data privacy and consent, the "High-Quality Data Curation Pipeline" (Appendix, Sec. 1) describes collecting "raw videos from the Internet" and filtering them. The manuscript does not explicitly state the legal basis for this data collection, nor does it confirm whether the authors obtained IRB/IACUC approval or informed consent from the individuals appearing in the training videos. Given the use of human subjects, this is a critical omission. The authors must clarify the source of the data, the licensing terms, and the steps taken to ensure compliance with privacy regulations (e.g., GDPR, CCPA) and ethical standards for human subject research.

Furthermore, the construction of the HGC-Bench benchmark involves "anonymizing identifiable facial information via face swapping" (Appendix, "HGC-Bench Details"). While this is a positive step, the authors should provide evidence or a detailed explanation of the anonymization process's efficacy to ensure that re-identification is not possible. A statement on the residual risks of privacy leakage would strengthen the ethical standing of the work. Finally, the use of VLMs (Gemini-3.1/3.0) for automated captioning and validity checks introduces potential biases; the authors should briefly discuss how they monitored for and mitigated bias in these automated annotations.
