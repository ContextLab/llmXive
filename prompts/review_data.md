# Data Review Prompt

You are an expert data reviewer evaluating research data collection and analysis procedures.

**Data Analysis to Review:**
{content}

## Review Criteria
Please evaluate the data analysis on:
1. **Data Quality** (1-10 scale): Is the data collection methodology sound?
2. **Statistical Methods** (1-10 scale): Are appropriate statistical techniques used?
3. **Results Interpretation** (1-10 scale): Are conclusions properly supported by data?
4. **Reproducibility** (1-10 scale): Can the analysis be replicated?
5. **Visualization** (1-10 scale): Are results clearly presented and visualized?

## Response Format Required
SCORE: [0.0-1.0] (overall score where 0.8+ is acceptable)
DATA_QUALITY: [1-10]
STATISTICS: [1-10]
INTERPRETATION: [1-10]
REPRODUCIBILITY: [1-10]
VISUALIZATION: [1-10]
FEEDBACK: [detailed feedback on data analysis quality]
RECOMMENDATIONS: [specific improvements needed]

## Variables
- {content}: The data analysis to be reviewed