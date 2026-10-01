import os
import sys
import subprocess
import tempfile
import logging
import time
import yaml
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

# Configuration imports
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/failures.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class ScanTimeoutError(Exception):
    """Raised when a scanner exceeds its timeout limit."""
    pass

class UnsupportedLanguageError(Exception):
    """Raised when a snippet's language is not supported by the scanner."""
    pass

class ScannerExecutionError(Exception):
    """Raised when a scanner fails to execute or produces no valid output."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout events."""
    raise ScanTimeoutError("Scanner execution timed out")

def load_severity_map() -> Dict[str, int]:
    """Load the NIST severity mapping from the YAML file."""
    map_path = Path(config.PROJECT_ROOT) / "data" / "mappings" / "nist_severity_map.yaml"
    if not map_path.exists():
        logger.error(f"Severity map not found at {map_path}")
        raise FileNotFoundError(f"Severity map not found: {map_path}")
    
    with open(map_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('mapping', {})

def map_severity_to_ordinal(raw_severity: str, severity_map: Dict[str, int]) -> int:
    """Map raw scanner severity to NIST ordinal rank."""
    return severity_map.get(raw_severity, 0)

def detect_language(code_snippet: str) -> str:
    """
    Detect programming language based on heuristics or file extension hints.
    Returns: 'python', 'java', 'javascript', or 'unknown'
    """
    # Simple heuristics based on common patterns
    code_lower = code_snippet.lower()
    
    if 'import ' in code_lower and ('def ' in code_lower or 'class ' in code_lower):
        return 'python'
    elif 'package ' in code_lower or 'public class ' in code_lower:
        return 'java'
    elif 'function ' in code_lower or 'const ' in code_lower or 'let ' in code_lower:
        return 'javascript'
    elif code_snippet.strip().startswith('#!'):
        shebang = code_snippet.split('\n')[0]
        if 'python' in shebang:
            return 'python'
        elif 'java' in shebang:
            return 'java'
    
    return 'unknown'

def run_bandit(code_snippet: str, timeout_seconds: int = 60) -> Tuple[List[Dict], bool]:
    """
    Run Bandit static analysis on Python code.
    Returns: (findings_list, success_flag)
    """
    if detect_language(code_snippet) != 'python':
        return [], False  # Not a Python snippet, skip Bandit
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code_snippet)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['bandit', '-f', 'json', temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if result.returncode == 0 or result.returncode == 1:  # 1 means findings found
            findings = json.loads(result.stdout)
            return findings.get('results', []), True
        else:
            logger.warning(f"Bandit execution failed for snippet: {result.stderr}")
            return [], False
    except subprocess.TimeoutExpired:
        raise ScanTimeoutError("Bandit scan timed out")
    except Exception as e:
        logger.error(f"Bandit execution error: {str(e)}")
        return [], False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def run_semgrep(code_snippet: str, language: str, timeout_seconds: int = 60) -> Tuple[List[Dict], bool]:
    """
    Run Semgrep static analysis.
    Returns: (findings_list, success_flag)
    """
    ext_map = {'python': '.py', 'java': '.java', 'javascript': '.js'}
    ext = ext_map.get(language, '.txt')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.write(code_snippet)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['semgrep', '--config', 'p/security-audit', '--json', temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if result.returncode == 0 or result.returncode == 1:
            findings = json.loads(result.stdout)
            return findings.get('results', []), True
        else:
            logger.warning(f"Semgrep execution failed: {result.stderr}")
            return [], False
    except subprocess.TimeoutExpired:
        raise ScanTimeoutError("Semgrep scan timed out")
    except json.JSONDecodeError:
        logger.error("Semgrep produced invalid JSON output")
        return [], False
    except Exception as e:
        logger.error(f"Semgrep execution error: {str(e)}")
        return [], False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def run_codeql(code_snippet: str, language: str, timeout_seconds: int = 120) -> Tuple[List[Dict], bool]:
    """
    Run CodeQL static analysis.
    Returns: (findings_list, success_flag)
    """
    # CodeQL requires a database, so we simulate the check or skip if not configured
    # For this implementation, we'll return empty results if CodeQL isn't fully set up
    # In a full implementation, this would create a temp database and run queries
    
    if language not in ['java', 'javascript']:
        return [], False
    
    # Placeholder for actual CodeQL execution
    # In production, this would involve:
    # 1. Creating a temp directory
    # 2. Initializing a CodeQL database
    # 3. Running security queries
    # 4. Parsing results
    
    logger.info(f"CodeQL analysis skipped for snippet (requires full setup): {language}")
    return [], False

def analyze_snippets(snippets: List[Dict], severity_map: Dict[str, int], 
                    timeout_per_scan: int = 60) -> List[Dict]:
    """
    Analyze a list of code snippets using multiple scanners.
    Handles failures and logs them appropriately.
    
    Args:
        snippets: List of dicts with keys: snippet_id, model, prompt_id, code, language
        severity_map: NIST severity mapping
        timeout_per_scan: Timeout in seconds per scanner run
    
    Returns:
        List of finding records with mapped severities
    """
    all_findings = []
    finding_id_counter = 1
    
    for snippet in snippets:
        snippet_id = snippet.get('snippet_id')
        code = snippet.get('code', '')
        model = snippet.get('model')
        prompt_id = snippet.get('prompt_id')
        
        # Check for empty snippets
        if not code or not code.strip():
            logger.error(f"Empty snippet detected: {snippet_id} (Model: {model}, Prompt: {prompt_id})")
            continue
        
        # Detect language
        language = detect_language(code)
        if language == 'unknown':
            logger.warning(f"Unsupported language detected, skipping: {snippet_id} (Model: {model}, Prompt: {prompt_id})")
            continue
        
        snippet_findings = []
        
        # Run Bandit
        try:
            bandit_results, bandit_success = run_bandit(code, timeout_per_scan)
            if bandit_success:
                for result in bandit_results:
                    raw_sev = result.get('issue_severity', 'MEDIUM')
                    mapped_rank = map_severity_to_ordinal(raw_sev, severity_map)
                    snippet_findings.append({
                        'finding_id': f'F{finding_id_counter:05d}',
                        'snippet_id': snippet_id,
                        'scanner': 'bandit',
                        'cwe_id': result.get('cwe', {}).get('id', 'UNKNOWN'),
                        'raw_severity': raw_sev,
                        'mapped_ordinal_rank': mapped_rank,
                        'finding_text': result.get('issue_text', 'No description')
                    })
                    finding_id_counter += 1
        except ScanTimeoutError as e:
            logger.error(f"Bandit timeout for snippet {snippet_id}: {str(e)}")
        except ScannerExecutionError as e:
            logger.error(f"Bandit execution error for snippet {snippet_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Bandit for snippet {snippet_id}: {str(e)}")
        
        # Run Semgrep
        try:
            semgrep_results, semgrep_success = run_semgrep(code, language, timeout_per_scan)
            if semgrep_success:
                for result in semgrep_results:
                    raw_sev = result.get('severity', 'MEDIUM')
                    mapped_rank = map_severity_to_ordinal(raw_sev, severity_map)
                    snippet_findings.append({
                        'finding_id': f'F{finding_id_counter:05d}',
                        'snippet_id': snippet_id,
                        'scanner': 'semgrep',
                        'cwe_id': result.get('extra', {}).get('metadata', {}).get('cwe', 'UNKNOWN'),
                        'raw_severity': raw_sev,
                        'mapped_ordinal_rank': mapped_rank,
                        'finding_text': result.get('extra', {}).get('message', 'No description')
                    })
                    finding_id_counter += 1
        except ScanTimeoutError as e:
            logger.error(f"Semgrep timeout for snippet {snippet_id}: {str(e)}")
        except ScannerExecutionError as e:
            logger.error(f"Semgrep execution error for snippet {snippet_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Semgrep for snippet {snippet_id}: {str(e)}")
        
        # Run CodeQL (only for supported languages)
        if language in ['java', 'javascript']:
            try:
                codeql_results, codeql_success = run_codeql(code, language, timeout_per_scan * 2)
                if codeql_success:
                    for result in codeql_results:
                        raw_sev = result.get('severity', 'MEDIUM')
                        mapped_rank = map_severity_to_ordinal(raw_sev, severity_map)
                        snippet_findings.append({
                            'finding_id': f'F{finding_id_counter:05d}',
                            'snippet_id': snippet_id,
                            'scanner': 'codeql',
                            'cwe_id': result.get('cwe', 'UNKNOWN'),
                            'raw_severity': raw_sev,
                            'mapped_ordinal_rank': mapped_rank,
                            'finding_text': result.get('message', 'No description')
                        })
                        finding_id_counter += 1
            except ScanTimeoutError as e:
                logger.error(f"CodeQL timeout for snippet {snippet_id}: {str(e)}")
            except ScannerExecutionError as e:
                logger.error(f"CodeQL execution error for snippet {snippet_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error in CodeQL for snippet {snippet_id}: {str(e)}")
        
        all_findings.extend(snippet_findings)
    
    return all_findings

def main():
    """Main entry point for the analysis pipeline."""
    logger.info("Starting vulnerability analysis pipeline...")
    
    # Load severity map
    try:
        severity_map = load_severity_map()
    except FileNotFoundError as e:
        logger.error(f"Failed to load severity map: {str(e)}")
        sys.exit(1)
    
    # Load generated snippets
    snippets_path = Path(config.PROJECT_ROOT) / "data" / "generated" / "snippets.csv"
    if not snippets_path.exists():
        logger.error(f"Snippets file not found: {snippets_path}")
        sys.exit(1)
    
    try:
        snippets_df = pd.read_csv(snippets_path)
        snippets = snippets_df.to_dict('records')
    except Exception as e:
        logger.error(f"Failed to load snippets: {str(e)}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(snippets)} snippets for analysis")
    
    # Get timeout configuration from config or default
    timeout_per_scan = getattr(config, 'SCANNER_TIMEOUT', 60)
    
    # Analyze snippets
    findings = analyze_snippets(snippets, severity_map, timeout_per_scan)
    
    # Save findings
    findings_path = Path(config.PROJECT_ROOT) / "data" / "findings" / "raw_findings.csv"
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    
    if findings:
        findings_df = pd.DataFrame(findings)
        findings_df.to_csv(findings_path, index=False)
        logger.info(f"Saved {len(findings)} findings to {findings_path}")
    else:
        logger.warning("No findings generated from analysis")
        # Still create an empty file with headers
        pd.DataFrame(columns=[
            'finding_id', 'snippet_id', 'scanner', 'cwe_id', 
            'raw_severity', 'mapped_ordinal_rank', 'finding_text'
        ]).to_csv(findings_path, index=False)
    
    logger.info("Analysis pipeline completed")

if __name__ == "__main__":
    main()