# Human Annotation Protocol: Prosocial Action and Negative Sentiment

## 1. Overview

This protocol defines the operational criteria for human raters to validate automated metrics in the study "The Effect of Priming on Prosocial Behavior in Online Communities." Raters will annotate a stratified sample of Reddit comments to assess the accuracy of:
1. **Prosocial Action Count**: The number of distinct prosocial actions offered or requested.
2. **Negative Sentiment Score**: The degree of negativity expressed in the comment.

**Goal**: To compute Cohen’s Kappa (inter-rater reliability) and Pearson correlation (against automated VADER scores) to ensure the automated pipeline meets the validity threshold (Kappa ≥ 0.70).

## 2. Definitions

### 2.1 Prosocial Action
A "Prosocial Action" is defined as a concrete, actionable offer to help, support, or engage in a beneficial behavior for another user or the community.

**Inclusion Criteria (Count as 1 Action):**
* **Direct Offers**: "I can help you with...", "Send me a DM, I'll...", "I will support you by..."
* **Resource Sharing**: "Here is a link to...", "You can find support at...", "I have a document..."
* **Emotional Support Offers**: "I'm here if you need to talk," "We can work through this together."
* **Advice with Actionable Steps**: "You should call...", "Try doing X..." (Must include a specific step, not just general sympathy).

**Exclusion Criteria (Do NOT count):**
* **General Sympathy**: "I'm sorry to hear that," "That sucks," "Rough day." (No action offered).
* **Vague Statements**: "Things will get better," "Stay strong."
* **Self-Disclosure without Offer**: "I went through this too." (Unless followed by an offer to help).
* **Negated Actions**: "I *cannot* help," "I *don't* want to support."
* **Prime Keywords in Isolation**: The words "help," "support," or "charity" appearing in the context of the *Prime* condition (e.g., "I am in a help thread") without an actual action being performed.

**Counting Rules**:
* If a comment offers multiple distinct actions (e.g., "I can listen to you *and* I can send you resources"), count as **2**.
* If the comment requests help for *others* (e.g., "Does anyone want to help this charity?"), count as **1**.
* If the comment is a request for help for *self* (e.g., "Can someone help me?"), count as **0** (this is a request, not an action performed by the commenter).

### 2.2 Negative Sentiment
Negative sentiment is defined as the expression of unfavorable feelings, hostility, distress, or criticism.

**Inclusion Criteria (Score High):**
* **Hostility/Aggression**: Insults, threats, or aggressive language.
* **Distress/Sadness**: Expressions of deep sadness, hopelessness, or pain.
* **Criticism**: Negative evaluation of a person, group, or situation.
* **Fear/Anxiety**: Expressions of worry or fear.

**Exclusion Criteria (Score Low/Neutral):**
* **Objective Statements**: Factual reporting without emotional coloring.
* **Positive/Neutral Context**: "I am not happy" (negation of negative) vs "I am sad".
* **Sarcasm**: If sarcasm is used to convey positivity, score as positive. If used to convey negativity, score as negative.

**Scale**:
Raters will assign a score from **0 to 5**:
* **0**: No negative sentiment (Positive or Neutral).
* **1**: Very slight negative sentiment (mild annoyance).
* **2**: Moderate negative sentiment (sadness, clear criticism).
* **3**: Strong negative sentiment (anger, distress).
* **4**: Very strong negative sentiment (hostility, severe distress).
* **5**: Extreme negative sentiment (abusive, threatening).

## 3. Annotation Procedure

1. **Access**: Log in to the annotation interface and load the assigned batch of comments (from `data/validation/gold_standard.csv`).
2. **Context**: Read the full comment. If the comment is short (< 10 words) and ambiguous, read the immediate parent thread context (provided in the `context` column).
3. **Step 1 - Prosocial Action**:
 * Scan for actionable offers.
 * Count distinct actions.
 * Enter integer count in `rater_prosocial_count`.
4. **Step 2 - Negative Sentiment**:
 * Assess the emotional tone.
 * Select the integer score (0-5) in `rater_neg_score`.
5. **Confidence**: If unsure, mark `confidence` as "Low", otherwise "High".
6. **Submit**: Save the annotation and move to the next item.

## 4. Quality Control & Abort Conditions

* **Inter-Rater Reliability**: Reliability will be calculated on the overlap between raters.
* **Threshold**: If Cohen's Kappa < 0.70 for either metric, the pipeline will abort, and the annotation protocol will be revised.
* **Disagreement Resolution**: Comments with high disagreement (e.g., one rater counts 0 actions, another counts 3) will be flagged for a third senior rater adjudication.

## 5. Data Privacy & Ethics

* **Anonymization**: All user IDs in the dataset have been replaced with SHA-256 hashes. Do not attempt to reverse-engineer identities.
* **Content**: Comments may contain sensitive topics. Raters should take breaks if content becomes distressing.
* **Confidentiality**: Do not share or publish the raw comments or annotation data outside the secure research environment.

## 6. Example Annotations

**Example 1**
* *Comment*: "That is terrible. I am so sorry you are going through this. If you need someone to talk to, DM me."
* *Prosocial Count*: 1 (The offer "DM me" is a concrete action).
* *Neg Score*: 2 (Moderate sadness/empathy, but the action is positive).

**Example 2**
* *Comment*: "You are an idiot for posting this. Nobody cares."
* *Prosocial Count*: 0.
* *Neg Score*: 5 (Extreme hostility).

**Example 3**
* *Comment*: "I can't help you, I'm busy."
* *Prosocial Count*: 0 (Explicitly negated).
* *Neg Score*: 1 (Slight negativity/rudeness).

**Example 4**
* *Comment*: "Here is the link to the charity: [link]. Also, I will donate $10 on your behalf."
* *Prosocial Count*: 2 (Sharing a resource + donating money).
* *Neg Score*: 0.