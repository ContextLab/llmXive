"""
Prompt templates for query reformulation based on static analysis signals.

This module provides templates for generating reformulated queries for the
iterative agent loop (US2). It consumes static analysis signals from 
code/agent/static_analysis.py to construct context-aware prompts.
"""

from typing import Dict, List, Optional, Any
from jinja2 import Template
import textwrap

# Static Analysis Signal Types
SIGNAL_TYPE_SYNTAX_ERROR = "syntax_error"
SIGNAL_TYPE_UNDEFINED_VARIABLE = "undefined_variable"
SIGNAL_TYPE_MISSING_IMPORT = "missing_import"
SIGNAL_TYPE_PYLINT_WARNING = "pylint_warning"

# Template: Base Reformulation Prompt
REFORMULATION_BASE_TEMPLATE = """
You are an AI coding agent tasked with resolving an issue in a repository.
You have previously attempted to solve this issue but encountered errors.

Current Issue Context:
----------------------
Issue ID: {{ issue_id }}
Original Query: {{ original_query }}

Previous Attempt Analysis:
-------------------------
The following static analysis signals were detected in your previous attempt:
{% for signal in analysis_signals %}
- Type: {{ signal.type }}
  Location: {{ signal.location }}
  Message: {{ signal.message }}
  {% if signal.suggestion %}
  Suggested Fix: {{ signal.suggestion }}
  {% endif %}
{% endfor %}

Task:
-----
Based on the errors above, reformulate your approach to solve the issue.
1. Acknowledge the specific errors detected.
2. Propose a corrected strategy or code modification.
3. If the error suggests a missing import or undefined variable, explicitly state how you will address it.
4. Ensure your new query is self-contained and does not repeat the previous mistake.

Reformulated Query:
"""

# Template: Syntax Error Specific
REFORMULATION_SYNTAX_TEMPLATE = """
You encountered a syntax error in your previous attempt.

Error Details:
- File: {{ location }}
- Line: {{ line_number }}
- Message: {{ message }}

The code failed to parse. Review the code around line {{ line_number }}.
Common causes:
- Unclosed parentheses, brackets, or braces
- Missing colons after statements (if, for, def, class)
- Indentation errors
- Invalid characters or typos in keywords

Reformulate your query to fix this syntax error while maintaining the original intent of the solution.
"""

# Template: Undefined Variable Specific
REFORMULATION_UNDEFINED_VAR_TEMPLATE = """
You encountered an undefined variable error.

Error Details:
- Variable: {{ variable_name }}
- Location: {{ location }}

The variable '{{ variable_name }}' was used but not defined in the current scope.
Possible fixes:
1. Define the variable before use.
2. Import the variable from another module if it belongs there.
3. Check for typos in the variable name.

Reformulate your query to ensure '{{ variable_name }}' is properly defined or imported.
"""

# Template: Missing Import Specific
REFORMULATION_MISSING_IMPORT_TEMPLATE = """
You encountered a missing import error.

Error Details:
- Missing Module: {{ module_name }}
- Location: {{ location }}

The module '{{ module_name }}' is used but not imported.
Action required:
Add the appropriate import statement at the top of the file.
Example: `import {{ module_name }}` or `from {{ module_name }} import ...`

Reformulate your query to include the necessary imports.
"""

# Template: General Pylint/Static Analysis Warning
REFORMULATION_PYLINT_TEMPLATE = """
Static analysis detected potential issues in your code.

Warning Details:
- Type: {{ message_type }}
- Location: {{ location }}
- Message: {{ message }}

While the code may run, this warning suggests a potential bug or style violation.
Address this warning in your reformulated approach to ensure robust code.
"""

# Template: Loop Detection / Repeated Query
REFORMULATION_LOOP_DETECTION_TEMPLATE = """
WARNING: You have generated a query that is very similar to a previous attempt.

Previous Query: {{ previous_query }}
Current Attempt: {{ current_query }}

Similarity Score: {{ similarity_score }}

This suggests you may be stuck in a loop. You must significantly change your approach.
- Try a different strategy entirely.
- Re-read the issue description for missed details.
- Consider if the problem requires a different file or a broader context change.

Provide a distinctly different reformulated query.
"""

def format_reformulation_prompt(
    issue_id: str,
    original_query: str,
    analysis_signals: List[Dict[str, Any]],
    loop_detected: bool = False,
    previous_query: Optional[str] = None,
    similarity_score: Optional[float] = None
) -> str:
    """
    Generates a reformulation prompt based on static analysis signals.
    
    Args:
        issue_id: The unique identifier for the issue.
        original_query: The initial query sent to the agent.
        analysis_signals: List of static analysis signals (dicts with type, location, message, etc.).
        loop_detected: Boolean indicating if a query loop was detected.
        previous_query: The query from the previous turn (if loop detected).
        similarity_score: Similarity score between previous and current query (if loop detected).
        
    Returns:
        A formatted string prompt for the LLM to generate a reformulated query.
    """
    base_template = Template(REFORMULATION_BASE_TEMPLATE)
    base_prompt = base_template.render(
        issue_id=issue_id,
        original_query=original_query,
        analysis_signals=analysis_signals
    )
    
    specific_prompts = []
    
    for signal in analysis_signals:
        signal_type = signal.get("type", "")
        location = signal.get("location", "Unknown")
        message = signal.get("message", "")
        
        if signal_type == SIGNAL_TYPE_SYNTAX_ERROR:
            tmpl = Template(REFORMULATION_SYNTAX_TEMPLATE)
            specific_prompts.append(tmpl.render(
                location=location,
                line_number=signal.get("line_number", "Unknown"),
                message=message
            ))
        elif signal_type == SIGNAL_TYPE_UNDEFINED_VARIABLE:
            tmpl = Template(REFORMULATION_UNDEFINED_VAR_TEMPLATE)
            specific_prompts.append(tmpl.render(
                variable_name=signal.get("variable_name", "Unknown"),
                location=location,
                message=message
            ))
        elif signal_type == SIGNAL_TYPE_MISSING_IMPORT:
            tmpl = Template(REFORMULATION_MISSING_IMPORT_TEMPLATE)
            specific_prompts.append(tmpl.render(
                module_name=signal.get("module_name", "Unknown"),
                location=location,
                message=message
            ))
        elif signal_type == SIGNAL_TYPE_PYLINT_WARNING:
            tmpl = Template(REFORMULATION_PYLINT_TEMPLATE)
            specific_prompts.append(tmpl.render(
                message_type=signal.get("message_type", "Warning"),
                location=location,
                message=message
            ))
    
    loop_prompt = ""
    if loop_detected and previous_query:
        tmpl = Template(REFORMULATION_LOOP_DETECTION_TEMPLATE)
        loop_prompt = tmpl.render(
            previous_query=previous_query,
            current_query=original_query, # or current attempt if available
            similarity_score=similarity_score
        )
    
    full_prompt = base_prompt + "\n" + "\n".join(specific_prompts)
    if loop_prompt:
        full_prompt += "\n" + loop_prompt
        
    return full_prompt

def get_signal_summary(analysis_signals: List[Dict[str, Any]]) -> str:
    """
    Creates a concise summary of static analysis signals for logging or context.
    
    Args:
        analysis_signals: List of static analysis signals.
        
    Returns:
        A string summarizing the errors found.
    """
    if not analysis_signals:
        return "No static analysis errors detected."
    
    summary_parts = []
    for signal in analysis_signals:
        signal_type = signal.get("type", "unknown")
        message = signal.get("message", "")
        location = signal.get("location", "")
        summary_parts.append(f"[{signal_type}] {location}: {message}")
        
    return "; ".join(summary_parts)

def main():
    """
    CLI entry point for testing prompt generation.
    """
    sample_signals = [
        {
            "type": SIGNAL_TYPE_SYNTAX_ERROR,
            "location": "solver.py:42",
            "message": "invalid syntax",
            "line_number": 42
        },
        {
            "type": SIGNAL_TYPE_UNDEFINED_VARIABLE,
            "location": "solver.py:45",
            "message": "name 'x' is not defined",
            "variable_name": "x"
        }
    ]
    
    prompt = format_reformulation_prompt(
        issue_id="SWE-EXP-001",
        original_query="Fix the bug in the calculator",
        analysis_signals=sample_signals
    )
    
    print("Generated Reformulation Prompt:")
    print("-" * 40)
    print(prompt)

if __name__ == "__main__":
    main()