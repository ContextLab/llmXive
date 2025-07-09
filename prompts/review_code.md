# Code Review Prompt

You are an expert code reviewer evaluating research code for quality, correctness, and reproducibility.

**Code to Review:**
{content}

## Review Criteria
Please evaluate the code on:
1. **Correctness** (1-10 scale): Is the code logically sound and bug-free?
2. **Code Quality** (1-10 scale): Is it well-structured, readable, and maintainable?
3. **Documentation** (1-10 scale): Are comments, docstrings, and documentation adequate?
4. **Testing** (1-10 scale): Are there appropriate tests and error handling?
5. **Reproducibility** (1-10 scale): Can others easily run and reproduce results?

## Response Format Required
SCORE: [0.0-1.0] (overall score where 0.8+ is acceptable)
CORRECTNESS: [1-10]
QUALITY: [1-10]
DOCUMENTATION: [1-10]
TESTING: [1-10]
REPRODUCIBILITY: [1-10]
FEEDBACK: [detailed feedback on code quality and issues]
RECOMMENDATIONS: [specific improvements needed]

## Variables
- {content}: The code to be reviewed