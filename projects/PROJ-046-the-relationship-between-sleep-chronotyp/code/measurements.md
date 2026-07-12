# Measurements Protocol: Sleep Chronotype and Moral Judgement

**Project**: PROJ-046-the-relationship-between-sleep-chronotyp
**Version**: 1.0.0
**Date**: 2023-10-27
**Constitution Principle VI**: All psychometric instruments must be administered with exact versioning, strict item ordering, and transparent scoring formulas to ensure reproducibility.

---

## 1. Morningness-Eveningness Questionnaire (MEQ)

### 1.1 Instrument Specification
- **Full Name**: Horne & Ostberg Morningness-Eveningness Questionnaire
- **Version**: Original 1976 version (Self-assessment)
- **Source**: Horne, J. A., & Ostberg, O. (1976). A self-assessment questionnaire to determine morningness–eveningness in human circadian rhythms. *International Journal of Chronobiology*, 4(2), 97–110.
- **Item Count**: 19 items
- **Response Format**: Mixed (Likert scales, time-of-day selection, categorical choices)
- **Scoring Range**: 16 (Extreme Evening) to 86 (Extreme Morning)

### 1.2 Item Ordering and Response Scoring
The items must be presented in the exact order below. The scoring weights are applied as follows:

| Item # | Description / Question Type | Scoring Logic / Weight |
|:--- |:--- |:--- |
| 1 | Preferred rising time | 4 points per hour shift (05:00=8, 06:00=7... 10:00=1, >10:00=0) |
| 2 | Preferred bed time | 4 points per hour shift (21:00=8, 22:00=7... 02:00=1, >02:00=0) |
| 3 | Best time for physical exertion (50-55 min duration) | 05:00-10:00=1, 10:00-13:00=2, 13:00-17:00=3, 17:00-21:00=4 |
| 4 | Best time for mental exertion (1h duration) | 05:00-10:00=1, 10:00-13:00=2, 13:00-17:00=3, 17:00-21:00=4 |
| 5 | Time to feel fully awake (after waking) | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 6 | Time to feel fully alert (after waking) | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 7 | Breakfast preference | 07:00-08:00=4, 08:00-09:00=3, 09:00-10:00=2, >10:00=1 |
| 8 | Time to feel fully awake (after waking) - Alternative | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 9 | Time to feel fully alert (after waking) - Alternative | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 10 | Preferred bedtime (sleep onset) | 21:00-22:00=4, 22:00-23:00=3, 23:00-00:00=2, >00:00=1 |
| 11 | Preferred rising time (wake time) | 05:00-06:00=4, 06:00-07:00=3, 07:00-08:00=2, >08:00=1 |
| 12 | Best time for mental exertion (1h) | 05:00-10:00=1, 10:00-13:00=2, 13:00-17:00=3, 17:00-21:00=4 |
| 13 | Best time for physical exertion (50-55 min) | 05:00-10:00=1, 10:00-13:00=2, 13:00-17:00=3, 17:00-21:00=4 |
| 14 | Time to feel fully awake (after waking) | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 15 | Time to feel fully alert (after waking) | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 16 | Breakfast preference | 07:00-08:00=4, 08:00-09:00=3, 09:00-10:00=2, >10:00=1 |
| 17 | Time to feel fully awake (after waking) - Alternative | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 18 | Time to feel fully alert (after waking) - Alternative | <30m=4, 30-60m=3, 1-2h=2, >2h=1 |
| 19 | Preferred bedtime (sleep onset) - Alternative | 21:00-22:00=4, 22:00-23:00=3, 23:00-00:00=2, >00:00=1 |

*Note: Items 3, 4, 12, 13 are inverted in some versions; this protocol uses the standard Horne & Ostberg (1976) mapping where earlier times = higher morningness scores.*

### 1.3 Scoring Formula
The total MEQ score is the sum of the weighted scores for all 19 items.

$$ \text{MEQ}_{\text{total}} = \sum_{i=1}^{19} w_i(x_i) $$

Where $x_i$ is the raw response to item $i$, and $w_i$ is the mapping function defined in Section 1.2.

**Classification Thresholds:**
- **Definite Morning**: 59 – 86
- **Moderate Morning**: 53 – 58
- **Intermediate**: 42 – 52
- **Moderate Evening**: 35 – 41
- **Definite Evening**: 16 – 34

---

## 2. Moral Foundations Questionnaire (MFQ)

### 2.1 Instrument Specification
- **Full Name**: Moral Foundations Questionnaire (MFQ 2.0)
- **Version**: 2.0 (Graham et al., 2011)
- **Source**: Graham, J., Nosek, B. A., Haidt, J., Iyer, R., Koleva, S., & Ditto, P. H. (2011). Mapping the moral domain. *Journal of Personality and Social Psychology*, 101(2), 366–385.
- **Item Count**: 30 items (15 "Relevance" + 15 "Judgment")
- **Response Format**: 7-point Likert scale (0 = "Not at all relevant/Judge to be wrong" to 6 = "Extremely relevant/Judge to be very wrong")
- **Subscales**: 5 (Care/Harm, Fairness/Cheating, Loyalty/Betrayal, Authority/Subversion, Sanctity/Degradation)

### 2.2 Item Ordering and Response Scoring
Items are presented in the exact order below. The questionnaire consists of two blocks:
1. **Relevance Block**: Items 1-15 (How relevant is this consideration when you decide whether something is right or wrong?)
2. **Judgment Block**: Items 16-30 (To what extent do you agree with the following statements?)

**Scoring Keys:**
Each item maps to one of the 5 foundations. Some items are reverse-coded (indicated by `R`).

| Item # | Block | Foundation | Text Snippet | Reverse Code? |
|:--- |:--- |:--- |:--- |:--- |
| 1 | Relevance | Care | Whether or not someone suffered emotionally | No |
| 2 | Relevance | Fairness | Whether or not someone suffered injustice | No |
| 3 | Relevance | Loyalty | Whether or not someone acted disloyally | No |
| 4 | Relevance | Authority | Whether or not someone showed a lack of respect for authority | No |
| 5 | Relevance | Sanctity | Whether or not someone violated standards of purity and decency | No |
| 6 | Relevance | Care | Whether or not someone was compassionate | Yes |
| 7 | Relevance | Fairness | Whether or not someone was treated fairly | Yes |
| 8 | Relevance | Loyalty | Whether or not someone was loyal to their family | Yes |
| 9 | Relevance | Authority | Whether or not someone respected authority | Yes |
| 10 | Relevance | Sanctity | Whether or not someone acted to protect the weak and vulnerable | Yes |
| 11 | Relevance | Care | Whether or not someone was concerned about the suffering of others | No |
| 12 | Relevance | Fairness | Whether or not someone violated the rules of fairness | No |
| 13 | Relevance | Loyalty | Whether or not someone betrayed their group | No |
| 14 | Relevance | Authority | Whether or not someone disobeyed their leader | No |
| 15 | Relevance | Sanctity | Whether or not someone engaged in unnatural acts | No |
| 16 | Judgment | Care | Compassion for those who are suffering is the most important virtue | No |
| 17 | Judgment | Fairness | Justice is the most important requirement for a society | No |
| 18 | Judgment | Loyalty | It is more important to be a team player than to be yourself | No |
| 19 | Judgment | Authority | Respect for authority is something all children need to learn | No |
| 20 | Judgment | Sanctity | People should not do things that are disgusting, even if no one is harmed | No |
| 21 | Judgment | Care | It is more important to be kind than to be fair | No |
| 22 | Judgment | Fairness | It is more important to be fair than to be loyal | No |
| 23 | Judgment | Loyalty | It is more important to be loyal to your country than to be free | No |
| 24 | Judgment | Authority | It is more important to obey the law than to follow your conscience | No |
| 25 | Judgment | Sanctity | It is more important to be pure than to be happy | No |
| 26 | Judgment | Care | I am proud of my country's history | No |
| 27 | Judgment | Fairness | I believe in the rule of law | No |
| 28 | Judgment | Loyalty | I am proud of my family | No |
| 29 | Judgment | Authority | I believe in respecting authority | No |
| 30 | Judgment | Sanctity | I believe in purity | No |

*Note: The exact wording of items 10, 26-30 may vary slightly in translations, but the mapping to the "Sanctity" foundation remains consistent in the 2.0 version.*

### 2.3 Scoring Formula
For each subscale $S \in \{Care, Fairness, Loyalty, Authority, Sanctity\}$:

1. **Identify Items**: Select the 6 items (3 Relevance, 3 Judgment) mapped to $S$.
2. **Reverse Code**: For items marked `R`, compute $x'_{i} = 6 - x_{i}$.
3. **Sum**: Sum the raw (or reverse-coded) scores for the 6 items.
4. **Average**: Divide by 6 to get the subscale mean.

$$ \text{Score}_S = \frac{1}{6} \sum_{j \in \text{Items}_S} x'_{j} $$

**Output Format**:
The final dataset will include 5 continuous variables: `MFQ_Care`, `MFQ_Fairness`, `MFQ_Loyalty`, `MFQ_Authority`, `MFQ_Sanctity`.
Range: 0.0 to 6.0.

---

## 3. Data Integrity and Quality Control

- **Missing Data**: Any participant with >20% missing items on either MEQ or MFQ is excluded.
- **Outliers**: Scores outside the theoretical range (MEQ: 16-86, MFQ: 0-6) are flagged as data entry errors and excluded.
- **Consistency**: Reverse-coded items will be checked for consistency with forward-coded items within the same subscale.

---
*End of Measurements Protocol*