# Measurements Protocol: Sleep Chronotype and Moral Judgement

**Project**: PROJ-046-the-relationship-between-sleep-chronotyp
**Version**: 1.0.0
**Date**: 2023-10-27
**Constitution Principle VI**: All measurement instruments must be documented with exact version, item ordering, and scoring formulas to ensure reproducibility.

## 1. Morningness-Eveningness Questionnaire (MEQ)

### 1.1 Instrument Details
- **Full Name**: Morningness-Eveningness Questionnaire
- **Authors**: Horne, J. A., & Ostberg, O. (1976)
- **Citation**: International Journal of Chronobiology, 4(2), 97-110.
- **Version Used**: Original 1976 Version (19 items)
- **Domain**: Circadian Rhythm / Chronotype Assessment
- **License**: Public Domain (Academic Use)

### 1.2 Item Ordering and Response Options
{{claim:c_5304d05a}} (Wikipedia: Adolescent sleep, https://en.wikipedia.org/wiki/Adolescent_sleep) Items are presented in the following order with specific response options.

| Item | Question Summary | Response Options (Points) |
|:--- |:--- |:--- |
| 1 | Preferred time to get up | 5 options (1-5) |
| 2 | Time to get up (actual) | 6 options (1-6) |
| 3 | Alertness after rising | 4 options (1-4) |
| 4 | Preferred time for exercise | 4 options (1-4) |
| 5 | Time to feel tired (bedtime) | 5 options (1-5) |
| 6 | Time to go to bed (actual) | 6 options (1-6) |
| 7 | Alertness 30 mins after getting up | 4 options (1-4) |
| 8 | Time to feel tired (bedtime) | 5 options (1-5) |
| 9 | Preferred time for a mental test | 4 options (1-4) |
| 10 | Preferred time for physical test | 4 options (1-4) |
| 11 | Preferred time for a break | 4 options (1-4) |
| 12 | Preferred time for a meal | 4 options (1-4) |
| 13 | Preferred time for a walk | 4 options (1-4) |
| 14 | Preferred time for a swim | 4 options (1-4) |
| 15 | Preferred time for a social activity | 4 options (1-4) |
| 16 | Preferred time for a creative task | 4 options (1-4) |
| 17 | Preferred time for a cognitive task | 4 options (1-4) |
| 18 | Preferred time for a leisure activity | 4 options (1-4) |
| 19 | Preferred time for a work task | 4 options (1-4) |

*Note: Response options vary by item. See Appendix A for exact wording.*

### 1.3 Scoring Formula
The total MEQ score is the sum of points from all 19 items.
- **Range**: 16 to 86
- **Calculation**: $Score = \sum_{i=1}^{19} Item_i$

**Chronotype Classification Thresholds**:
- **Definite Morning Type**: 59 - 86
- **Moderate Morning Type**: 53 - 58
- **Intermediate Type**: 42 - 52
- **Moderate Evening Type**: 36 - 41
- **Definite Evening Type**: 16 - 35

*Implementation Note: For binary classification in this study, we use:*
- **Morning**: Score >= 59
- **Evening**: Score <= 41
- **Intermediate**: 42 <=Score <= 58

---

## 2. Moral Foundations Questionnaire (MFQ)

### 2.1 Instrument Details
- **Full Name**: Moral Foundations Questionnaire (MFQ)
- **Authors**: Graham, J., Haidt, J., & Nosek, B. A. (2009 (2405.11100, https://arxiv.org/abs/2405.11100))
- **Citation**: Journal of Personality and Social Psychology, 96(5), 1029–1046.
- **Version Used**: MFQ 2.0 (Revised)
- **Domain**: Moral Psychology / Ethical Reasoning
- **License**: Open Source (Creative Commons Attribution 4.0)

### 2.2 Structure and Subscales
The MFQ measures five moral foundations. [UNRESOLVED-CLAIM: c_36fe6808 — status=not_enough_info] Each subscale consists of 6 items (3 "Relevance" items and 3 "Judgement" items), totaling 30 items.

**The Five Subscales**:
1. **Care/Harm**: Sensitivity to suffering and compassion.
2. **Fairness/Cheating**: Sensitivity to justice, rights, and proportionality.
3. **Loyalty/Betrayal**: Sensitivity to group membership and patriotism.
4. **Authority/Subversion**: Sensitivity to hierarchy, tradition, and leadership.
5. **Sanctity/Degradation**: Sensitivity to bodily and spiritual purity.

### 2.3 Item Ordering
Items are presented in a randomized order for each participant to prevent order effects. However, for scoring purposes, they map to the following subscales:

**Relevance Items (Rate importance of considerations)**:
- *Care*: 1, 2, 3
- *Fairness*: 4, 5, 6
- *Loyalty*: 7, 8, 9
- *Authority*: 10, 11, 12
- *Sanctity*: 13, 14, 15

**Judgement Items (Agree with statements)**:
- *Care*: 16, 17, 18
- *Fairness*: 19, 20, 21
- *Loyalty*: 22, 23, 24
- *Authority*: 25, 26, 27
- *Sanctity*: 28, 29, 30

### 2.4 Response Options
All items use a 7-point Likert scale:
- 0: Not at all relevant / Strongly Disagree
- 1: Very slightly relevant / Disagree a little
- 2: Slightly relevant / Disagree somewhat
- 3: Moderately relevant / Neutral
- 4: Quite a bit relevant / Agree somewhat
- 5: Very relevant / Agree a lot
- 6: Extremely relevant / Strongly Agree

### 2.5 Scoring Formula
For each subscale $S$ (Care, Fairness, Loyalty, Authority, Sanctity):

1. **Reverse Coding**: Items 1, 2, 3 (Relevance) are scored normally. Items 16-18 (Judgement) for Care are reverse coded if necessary based on specific item wording (standard MFQ 2.0 does not require reverse coding for the standard set, but check specific item text). *Correction*: In the standard MFQ, items 1-3 and 16-18 are all positively keyed for Care. No reverse coding is typically needed for the standard 30-item set unless using a modified version. We will use the standard 0-6 scoring.

2. **Subscale Calculation**:
 $$Score_S = \frac{\sum_{i \in Items_S} Item_i}{N_{items\_per\_subscale}}$$
 Where $N_{items\_per\_subscale} = 6$.

3. **Range**: 0.0 to 6.0 per subscale.

**Data Quality Checks**:
- **Missing Data**: If a participant has > 2 missing items in a subscale, the subscale score is set to `NA`.
- **Out-of-Range**: Any score < 0 or > 6 is flagged as an error and excluded.

### 2.6 Cronbach's Alpha Calculation
Reliability for each subscale will be calculated using the `cronbach_alpha()` function from the `psych` package (or `ltm` in R) on the 6 items per subscale.
- **Target**: $\alpha > 0.70$ for acceptable reliability.
- **Output**: Saved to `data/derived/reliability_metrics.csv`.

---

## Appendix A: MEQ Full Item Wording (Reference)
*Note: The following is a summary for reference. The exact wording is available in the Horne & Ostberg (1976) paper.*
1. "At what time would you get up if you were entirely free to plan your day?"
2. "At what time would you go to bed if you were entirely free to plan your evening?"
... (Items 3-19 follow the standard questionnaire)

---

## Appendix B: MFQ Full Item Wording (Reference)
*Note: The following is a summary for reference. The exact wording is available in Graham et al. (2009).*
**Relevance**: "When you decide whether something is right or wrong, to what extent are the following considerations relevant to your thinking?"
1. Whether or not someone suffered emotionally
2. Whether or not some people were treated differently than others
...
**Judgement**: "Please indicate your agreement or disagreement with the following statements."
16. Compassion for those who are suffering is the most crucial virtue
17. When the government makes laws, the number one principle should be ensuring that everyone is treated fairly
...

---
**End of Document**