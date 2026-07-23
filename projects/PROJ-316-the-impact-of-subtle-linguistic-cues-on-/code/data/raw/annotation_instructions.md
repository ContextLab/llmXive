# Annotation Protocol: Perceived Authenticity

## 1. Scale Definition
Please rate the perceived authenticity of the following text on a **Likert Scale of 1 to 5**:

- **1 (Not Authentic)**: The text feels robotic, generic, evasive, or overly polished. It lacks a distinct "voice" or human-like nuance.
- **2 (Slightly Authentic)**: The text feels somewhat artificial but has minor human-like elements.
- **3 (Moderately Authentic)**: The text feels neutral. It could be human or AI; no strong signal either way.
- **4 (Mostly Authentic)**: The text feels human-like, showing personality, appropriate uncertainty, or natural flow.
- **5 (Highly Authentic)**: The text feels genuinely human, with strong voice, natural hedging (when appropriate), and emotional resonance.

## 2. Instructions for Raters
1. Read the full text of the conversation turn.
2. Ignore grammar errors or typos; focus on the *tone* and *phrasing*.
3. Consider if the speaker sounds like a real person or a machine.
4. Specifically, note if the use of hedging words (e.g., "maybe", "I think") feels natural (authentic) or forced (inauthentic).
5. Assign a score from 1 to 5 based on the scale above.
6. If the text is too short to judge, mark it as "Skip" (handled by the tool).

## 3. Sample Items

**Sample A (Likely Low Authenticity)**
> "I am a language model designed to assist you. I do not have feelings or personal experiences."
*Rating: 1* (Explicitly robotic, generic).

**Sample B (Likely High Authenticity)**
> "I'm not entirely sure, but I guess it might be the best option. What do you think?"
*Rating: 4 or 5* (Uses natural hedging, shows uncertainty).

**Sample C (Neutral)**
> "The weather is nice today. Let's go for a walk."
*Rating: 3* (Generic, could be either).

## 4. Hedge Identification (Secondary Task)
For the same text, please also identify if the text contains "hedging" words (uncertainty markers).
- If you see words like "maybe", "perhaps", "I think", "seem", "likely", etc., mark them.
- This is used to validate the automated hedge extraction.
