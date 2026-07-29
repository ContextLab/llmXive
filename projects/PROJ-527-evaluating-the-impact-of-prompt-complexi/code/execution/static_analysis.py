import os
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

SECURITY_RULES = [
    # Rule ID: pattern description
    ("SEC001", r'\beval\s*\(', "Use of eval() function"),
    ("SEC002", r'\bexec\s*\(', "Use of exec() function"),
    ("SEC003", r'__import__\s*\(', "Use of __import__() function"),
    ("SEC004", r'\bopen\s*\(\s*[\'"]r?[\'"]\s*,\s*[\'"]w[\'"]', "Dangerous file open mode"),
    ("SEC005", r'\bsubprocess\.call\s*\(', "Use of subprocess.call()"),
    ("SEC006", r'\bsubprocess\.Popen\s*\(', "Use of subprocess.Popen()"),
    ("SEC007", r'\bos\.system\s*\(', "Use of os.system()"),
    ("SEC008", r'\bos\.popen\s*\(', "Use of os.popen()"),
    # Hardcoded credential patterns
    ("SEC009", r'(?:password|passwd|pwd)\s*=\s*[\'"][^\'"]+[\'"]', "Hardcoded password"),
    ("SEC010", r'(?:api_key|apikey)\s*=\s*[\'"][^\'"]+[\'"]', "Hardcoded API key"),
    ("SEC011", r'(?:secret|secret_key)\s*=\s*[\'"][^\'"]+[\'"]', "Hardcoded secret"),
    ("SEC012", r'(?:token|auth_token)\s*=\s*[\'"][^\'"]+[\'"]', "Hardcoded token"),
    # SQL injection risks
    ("SEC013", r'\.\s*execute\s*\(\s*f[\'\"]', "F-string in SQL execute (potential SQL injection)"),
    ("SEC014", r'\.\s*execute\s*\(\s*%\s*\(.*\)', "String formatting in SQL execute (potential SQL injection)"),
    ("SEC015", r'\.\s*execute\s*\(\s*\+', "String concatenation in SQL execute (potential SQL injection)"),
]

def run_ruff_check(code_content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run ruff static analysis on the given code content.
    
    Args:
        code_content: The Python code to analyze.
        file_path: Optional path to the file (for ruff context).
        
    Returns:
        Dictionary containing ruff results.
    """
    if file_path is None:
        # Create a temporary file for analysis
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code_content)
            file_path = f.name
        temp_file_created = True
    else:
        temp_file_created = False

    try:
        result = subprocess.run(
            ['ruff', 'check', '--output-format=json', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return {"issues": [], "status": "clean"}
        
        try:
            issues = json.loads(result.stdout)
            return {"issues": issues, "status": "issues_found"}
        except json.JSONDecodeError:
            return {"issues": [], "status": "parse_error", "raw_output": result.stdout}
    except subprocess.TimeoutExpired:
        logger.warning(f"Ruff check timed out for {file_path}")
        return {"issues": [], "status": "timeout"}
    except Exception as e:
        logger.error(f"Error running ruff: {e}")
        return {"issues": [], "status": "error", "error": str(e)}
    finally:
        if temp_file_created:
            try:
                os.unlink(file_path)
            except OSError:
                pass

def analyze_generated_code(
    code_content: str,
    sample_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform comprehensive static analysis on generated code.
    
    This includes:
    1. Ruff checks for code quality and complexity metrics
    2. Security vulnerability scanning
    
    Args:
        code_content: The Python code to analyze.
        sample_id: Optional identifier for the code sample.
        
    Returns:
        Dictionary containing analysis results including:
        - cyclomatic_complexity: Estimated cyclomatic complexity
        - lines_of_code: Total lines of code
        - indentation_issues: List of indentation problems
        - security_vulnerabilities: List of security issues found
        - is_safe_for_execution: Boolean flag for manual review
    """
    # Run ruff for basic metrics
    ruff_result = run_ruff_check(code_content)
    
    # Initialize analysis result
    analysis = {
        "sample_id": sample_id,
        "cyclomatic_complexity": 0,
        "lines_of_code": len(code_content.splitlines()),
        "indentation_issues": [],
        "security_vulnerabilities": [],
        "is_safe_for_execution": True,
        "ruff_issues": ruff_result.get("issues", [])
    }
    
    # Extract cyclomatic complexity from ruff (using mccabe plugin if available)
    # Fallback to simple heuristic if not available
    try:
        # Try to get complexity from ruff output if mccabe plugin is enabled
        for issue in ruff_result.get("issues", []):
            if issue.get("code") == "C901":  # mccabe complexity
                analysis["cyclomatic_complexity"] = int(issue.get("message", "0").split()[-1])
                break
    except (ValueError, IndexError, TypeError):
        pass
    
    # If no complexity found, use a simple heuristic
    if analysis["cyclomatic_complexity"] == 0:
        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with', 'and', 'or']
        complexity = 1
        for keyword in decision_keywords:
            complexity += code_content.lower().count(f'\n{keyword} ') + code_content.lower().count(f'\n{keyword}\t')
        analysis["cyclomatic_complexity"] = complexity
    
    # Security vulnerability scanning
    security_issues = []
    for rule_id, pattern, description in SECURITY_RULES:
        import re
        matches = re.finditer(pattern, code_content, re.IGNORECASE)
        for match in matches:
            line_num = code_content[:match.start()].count('\n') + 1
            security_issues.append({
                "rule_id": rule_id,
                "description": description,
                "line": line_num,
                "match": match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
            })
    
    analysis["security_vulnerabilities"] = security_issues
    
    # Determine if code is safe for execution
    # Flag for manual review if any security vulnerabilities are found
    if security_issues:
        analysis["is_safe_for_execution"] = False
        logger.warning(f"Security vulnerabilities detected in sample {sample_id}: {len(security_issues)} issues")
    
    return analysis

def main():
    """
    Main entry point for static analysis module.
    This function demonstrates the usage of the static analysis functions.
    """
    # Example usage
    sample_code = """
    def vulnerable_function():
        password = "super_secret_123"
        api_key = "AKIAIOSFODNN7EXAMPLE"
        result = eval("1 + 1")
        return result
    """
    
    result = analyze_generated_code(sample_code, sample_id="example-001")
    
    print(f"Analysis Result for example-001:")
    print(f"  Lines of Code: {result['lines_of_code']}")
    print(f"  Cyclomatic Complexity: {result['cyclomatic_complexity']}")
    print(f"  Security Vulnerabilities: {len(result['security_vulnerabilities'])}")
    print(f"  Safe for Execution: {result['is_safe_for_execution']}")
    
    if result['security_vulnerabilities']:
        print("\nVulnerabilities found:")
        for vuln in result['security_vulnerabilities']:
            print(f"  - {vuln['rule_id']}: {vuln['description']} at line {vuln['line']}")

if __name__ == "__main__":
    main()