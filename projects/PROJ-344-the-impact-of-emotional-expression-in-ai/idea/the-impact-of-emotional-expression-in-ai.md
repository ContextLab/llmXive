---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Emotional Expression in AI Avatars on User Trust

**Field**: psychology

## Research question

How does the synchrony between vocal tone and facial emotional expression in AI avatars influence users' trust in the avatar's advice?

## Motivation

Users increasingly interact with AI systems through embodied avatars that display emotional cues, yet we lack evidence on whether the *believability* of those cues—specifically, the alignment of vocal and facial signals—affects trust outcomes. This gap matters because poorly-synchronized emotional displays could undermine adoption of AI assistants in high-stakes domains like healthcare or education, where trust is essential.

## Literature gap analysis

### What we searched

Searched Semantic Scholar, arXiv, and OpenAlex using queries: (1) "emotional synchrony AI avatar trust", (2) "facial vocal expression consistency human-AI interaction", and (3) "multimodal emotional expression trust robot". Retrieved one result on emotional prosody and trust in robotic arm communication; no results directly on AI avatar facial-vocal synchrony and trust.

### What is known

- [Emotional Musical Prosody for the Enhancement of Trust in Robotic Arm Communication (2020)](http://arxiv.org/abs/2009.09048v1) — Establishes that emotional prosody can enhance trust in human-robot interaction, but focuses on industrial robotic arms rather than embodied conversational avatars.

### What is NOT known

No published work has measured how *cross-modal emotional synchrony* (alignment between facial expression and vocal tone) in AI avatars affects user trust. Existing trust research in HAI either uses static facial displays or unimodal audio cues, leaving the multimodal alignment question unaddressed.

### Why this gap matters

Filling this gap would inform design guidelines for AI companions in sensitive contexts (therapy, education, customer support) where trust is critical. Understanding whether synchrony matters—or whether any emotional display suffices—could prevent wasted development effort on unnecessary multimodal fidelity.

### How this project addresses the gap

This project will quantify emotional synchrony from existing human-AI interaction datasets and correlate it with user trust scores, producing the first empirical evidence on whether cross-modal alignment affects trust in avatar-based AI systems.

## Expected results

We expect to find either a positive correlation between synchrony and trust (supporting the "believability matters" hypothesis) or no significant relationship (suggesting emotional presence alone suffices). Either outcome will be publishable as it constrains design theory for trustworthy AI.

## Methodology sketch

- Download existing human-AI interaction datasets from OpenML or HuggingFace Datasets that include video/audio of avatar interactions with user trust ratings (e.g., search for "human-robot interaction trust dataset" on OpenML).
- Extract facial expression intensity scores using a pre-trained, CPU-compatible model (e.g., OpenFace or FER2013 classifier) from video frames.
- Extract vocal prosody features (pitch, energy, tempo) using librosa from audio tracks.
- Compute a synchrony metric: cross-correlation between facial expression time-series and vocal prosody time-series across each interaction segment.
- Aggregate synchrony scores per interaction and merge with user trust questionnaire scores (Likert scale) from the dataset metadata.
- Apply Spearman rank correlation to test the relationship between synchrony and trust (non-parametric to handle non-normal distributions).
- Run a robustness check: linear regression with control variables (avatar type, interaction duration, task difficulty) from dataset metadata.
- Generate scatter plots with confidence intervals and report correlation coefficients with 95% CI.

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: N/A (no prior fleshed-out ideas).
- Verdict: NOT a duplicate
