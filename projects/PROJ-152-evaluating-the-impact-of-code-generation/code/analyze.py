"""
Scanner Orchestration Module (T009)

Orchestrates Bandit, Semgrep, and CodeQL scans on generated code snippets.
Implements timeout handling per task requirement.
"""
import os
import sys
import subprocess
import tempfile
import logging
import time
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import config for path constants
import config
# Import generate module for TimeoutError if needed, though we define our own here for clarity
# The task requires timeout handling per scan.
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/analyze.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Timeout configuration (seconds) - Defined as per task requirement "A timeout per scan is established"
SCAN_TIMEOUT_SECONDS = 60

class ScanTimeoutError(Exception):
    """Exception raised when a scanner times out."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise ScanTimeoutError(f"Scan timed out after {SCAN_TIMEOUT_SECONDS} seconds")

def run_bandit(code_snippet: str, snippet_id: str) -> List[Dict[str, Any]]:
    """
    Run Bandit static analysis on Python code.
    
    Args:
        code_snippet: The Python code to analyze.
        snippet_id: Unique identifier for the snippet (used for temp file naming).
        
    Returns:
        List of findings dictionaries.
    """
    findings = []
    if not code_snippet or not code_snippet.strip():
        logger.warning(f"Empty snippet {snippet_id} skipped for Bandit.")
        return findings

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(code_snippet)
        tmp_path = tmp_file.name

    try:
        # Set signal for timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SCAN_TIMEOUT_SECONDS)

        try:
            # Run bandit
            # -f json for structured output
            # -r for recursive (not needed for single file but good practice)
            # -lll -ii (low and medium confidence) to catch more issues
            result = subprocess.run(
                ['bandit', '-f', 'json', '-r', '-lll', '-ii', tmp_path],
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT_SECONDS + 5, # Slight buffer for subprocess
                check=False
            )
            
            if result.returncode == 0 or result.returncode == 1: # 1 means issues found
                if result.stdout:
                    try:
                        bandit_output = json.loads(result.stdout)
                        for issue in bandit_output.get('results', []):
                            findings.append({
                                'scanner': 'bandit',
                                'cwe_id': issue.get('cwe', {}).get('id', 'UNKNOWN'),
                                'raw_severity': issue.get('severity', 'MEDIUM'),
                                'finding_text': issue.get('issue_text', 'No description'),
                                'line_number': issue.get('line_number', 0),
                                'confidence': issue.get('confidence', 'MEDIUM')
                            })
                    except json.JSONDecodeError:
                        logger.error(f"Bandit JSON parsing failed for {snippet_id}: {result.stderr}")
            else:
                logger.error(f"Bandit execution failed for {snippet_id}: {result.stderr}")
                
        except ScanTimeoutError as e:
            logger.warning(f"Bandit timed out for snippet {snippet_id}: {e}")
        except subprocess.TimeoutExpired as e:
            logger.warning(f"Bandit subprocess timed out for snippet {snippet_id}: {e}")
        finally:
            signal.alarm(0) # Cancel alarm

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    return findings

def run_semgrep(code_snippet: str, snippet_id: str, language_hint: str = 'python') -> List[Dict[str, Any]]:
    """
    Run Semgrep static analysis.
    
    Args:
        code_snippet: The code to analyze.
        snippet_id: Unique identifier.
        language_hint: Language hint for semgrep (default python).
        
    Returns:
        List of findings dictionaries.
    """
    findings = []
    if not code_snippet or not code_snippet.strip():
        logger.warning(f"Empty snippet {snippet_id} skipped for Semgrep.")
        return findings

    # Create temporary file
    suffix = '.py' if language_hint == 'python' else f'.{language_hint}'
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp_file:
        tmp_file.write(code_snippet)
        tmp_path = tmp_file.name

    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SCAN_TIMEOUT_SECONDS)

        try:
            # Run semgrep with security ruleset
            # --metrics=off to avoid telemetry issues in restricted envs
            result = subprocess.run(
                ['semgrep', 'scan', '--config=auto', '--metrics=off', '--json', tmp_path],
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT_SECONDS + 5,
                check=False
            )
            
            if result.returncode == 0 or result.returncode == 1:
                if result.stdout:
                    try:
                        semgrep_output = json.loads(result.stdout)
                        for result_item in semgrep_output.get('results', []):
                            findings.append({
                                'scanner': 'semgrep',
                                'cwe_id': result_item.get('extra', {}).get('metavars', {}).get('CWE', {}).get('value', 'UNKNOWN'),
                                'raw_severity': result_item.get('extra', {}).get('severity', 'MEDIUM'),
                                'finding_text': result_item.get('extra', {}).get('message', 'No description'),
                                'line_number': result_item.get('start', {}).get('line', 0),
                                'confidence': 'HIGH' # Semgrep confidence is implicit in rule match
                            })
                    except json.JSONDecodeError:
                        logger.error(f"Semgrep JSON parsing failed for {snippet_id}: {result.stderr}")
            else:
                logger.error(f"Semgrep execution failed for {snippet_id}: {result.stderr}")

        except ScanTimeoutError as e:
            logger.warning(f"Semgrep timed out for snippet {snippet_id}: {e}")
        except subprocess.TimeoutExpired as e:
            logger.warning(f"Semgrep subprocess timed out for snippet {snippet_id}: {e}")
        finally:
            signal.alarm(0)

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return findings

def run_codeql(code_snippet: str, snippet_id: str, language_hint: str = 'python') -> List[Dict[str, Any]]:
    """
    Run CodeQL analysis.
    
    Note: CodeQL requires a database and is heavy. For this implementation,
    we simulate the invocation structure or attempt a lightweight check if codeql is installed.
    Given the complexity of setting up a CodeQL DB in a script, we will check for the binary
    and run a basic query if possible, otherwise log a warning that CodeQL requires manual DB setup
    or is skipped in this lightweight mode.
    
    However, to satisfy the task "orchestrate CodeQL", we will attempt to run it if the binary exists.
    """
    findings = []
    if not code_snippet or not code_snippet.strip():
        logger.warning(f"Empty snippet {snippet_id} skipped for CodeQL.")
        return findings

    # Create temporary directory for DB
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, 'db')
    source_path = os.path.join(tmp_dir, 'source')
    os.makedirs(source_path, exist_ok=True)
    
    suffix = '.py' if language_hint == 'python' else f'.{language_hint}'
    source_file = os.path.join(source_path, f'snippet{suffix}')
    
    with open(source_file, 'w') as f:
        f.write(code_snippet)

    try:
        # Check if codeql is available
        try:
            subprocess.run(['codeql', 'version'], capture_output=True, check=True)
            codeql_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("CodeQL binary not found in PATH. Skipping CodeQL scan.")
            return findings

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SCAN_TIMEOUT_SECONDS)

        try:
            # 1. Database creation (might be slow, but necessary for CodeQL)
            # We use a very short timeout for DB creation or skip if it takes too long
            logger.info(f"Creating CodeQL database for {snippet_id}...")
            
            # This is a simplified approach. Real CodeQL requires a specific language pack.
            # We assume python-pack is installed.
            result_db = subprocess.run(
                ['codeql', 'database', 'create', db_path, f'--language={language_hint}', f'--source-root={source_path}', '--overwrite'],
                capture_output=True,
                text=True,
                timeout=30, # Short timeout for DB creation
                check=False
            )
            
            if result_db.returncode != 0:
                logger.warning(f"CodeQL DB creation failed for {snippet_id}: {result_db.stderr}")
                # If DB creation fails, we can't run queries.
                return findings

            # 2. Run a simple security query
            # We use a generic security query suite
            result_query = subprocess.run(
                ['codeql', 'database', 'analyze', db_path, '--format=csv', '--output=results.csv', 'codeql-security-queries'],
                capture_output=True,
                text=True,
                timeout=SCAN_TIMEOUT_SECONDS - 30, # Remaining time
                check=False
            )
            
            if result_query.returncode == 0:
                results_csv = os.path.join(tmp_dir, 'results.csv')
                if os.path.exists(results_csv):
                    with open(results_csv, 'r') as f:
                        lines = f.readlines()
                        # Skip header
                        for line in lines[1:]:
                            parts = line.strip().split(',')
                            if len(parts) >= 4:
                                findings.append({
                                    'scanner': 'codeql',
                                    'cwe_id': parts[0] if parts[0] else 'UNKNOWN',
                                    'raw_severity': 'MEDIUM', # CodeQL severity often in other fields, defaulting
                                    'finding_text': parts[3] if len(parts) > 3 else 'CodeQL finding',
                                    'line_number': int(parts[1]) if parts[1].isdigit() else 0,
                                    'confidence': 'HIGH'
                                })
            else:
                logger.warning(f"CodeQL query failed for {snippet_id}: {result_query.stderr}")

        except ScanTimeoutError as e:
            logger.warning(f"CodeQL timed out for snippet {snippet_id}: {e}")
        except subprocess.TimeoutExpired as e:
            logger.warning(f"CodeQL subprocess timed out for snippet {snippet_id}: {e}")
        finally:
            signal.alarm(0)

    finally:
        # Cleanup
        if os.path.exists(tmp_dir):
            import shutil
            shutil.rmtree(tmp_dir)

    return findings

def detect_language(code_snippet: str) -> str:
    """
    Simple heuristic to detect language from code snippet.
    Defaults to python if unknown.
    """
    if 'import ' in code_snippet or 'from ' in code_snippet:
        if 'java' in code_snippet.lower() or 'public class' in code_snippet:
            return 'java'
        if 'function' in code_snippet or 'const ' in code_snippet:
            return 'javascript'
    return 'python'

def analyze_snippets(snippets_data: List[Dict[str, Any]], output_path: str):
    """
    Main orchestration function to analyze a list of snippets.
    
    Args:
        snippets_data: List of dicts with keys: snippet_id, model, prompt_id, code
        output_path: Path to save the findings CSV.
    """
    all_findings = []
    finding_id_counter = 1

    logger.info(f"Starting analysis of {len(snippets_data)} snippets...")

    for snippet in snippets_data:
        snippet_id = snippet.get('snippet_id', 'unknown')
        code = snippet.get('code', '')
        
        if not code:
            logger.warning(f"Skipping empty snippet {snippet_id}")
            continue

        logger.info(f"Analyzing snippet {snippet_id}...")
        
        # Detect language
        lang = detect_language(code)
        logger.debug(f"Detected language for {snippet_id}: {lang}")

        # Run scanners
        # Bandit is Python only
        if lang == 'python':
            bandit_findings = run_bandit(code, snippet_id)
            all_findings.extend(bandit_findings)
        
        # Semgrep is multi-language
        semgrep_findings = run_semgrep(code, snippet_id, lang)
        all_findings.extend(semgrep_findings)

        # CodeQL is multi-language (heavy)
        codeql_findings = run_codeql(code, snippet_id, lang)
        all_findings.extend(codeql_findings)

        # Assign IDs and metadata
        for f in all_findings:
            # We need to attach snippet metadata to the finding
            # But since we are extending a list, we should do it before extending or map later.
            # Let's restructure: create findings with metadata immediately.
            pass

    # Re-process to attach metadata correctly
    final_findings = []
    for snippet in snippets_data:
        snippet_id = snippet.get('snippet_id')
        code = snippet.get('code', '')
        if not code: continue
        
        lang = detect_language(code)
        
        # Run Bandit
        if lang == 'python':
            raw_findings = run_bandit(code, snippet_id)
            for f in raw_findings:
                final_findings.append({
                    'finding_id': f'F{finding_id_counter:05d}',
                    'snippet_id': snippet_id,
                    'model': snippet.get('model', 'unknown'),
                    'prompt_id': snippet.get('prompt_id', 'unknown'),
                    'scanner': f['scanner'],
                    'cwe_id': f['cwe_id'],
                    'raw_severity': f['raw_severity'],
                    'mapped_ordinal_rank': 0, # To be filled by metrics.py later
                    'finding_text': f['finding_text'],
                    'line_number': f.get('line_number', 0)
                })
                finding_id_counter += 1

        # Run Semgrep
        raw_findings = run_semgrep(code, snippet_id, lang)
        for f in raw_findings:
            final_findings.append({
                'finding_id': f'F{finding_id_counter:05d}',
                'snippet_id': snippet_id,
                'model': snippet.get('model', 'unknown'),
                'prompt_id': snippet.get('prompt_id', 'unknown'),
                'scanner': f['scanner'],
                'cwe_id': f['cwe_id'],
                'raw_severity': f['raw_severity'],
                'mapped_ordinal_rank': 0,
                'finding_text': f['finding_text'],
                'line_number': f.get('line_number', 0)
            })
            finding_id_counter += 1

        # Run CodeQL
        raw_findings = run_codeql(code, snippet_id, lang)
        for f in raw_findings:
            final_findings.append({
                'finding_id': f'F{finding_id_counter:05d}',
                'snippet_id': snippet_id,
                'model': snippet.get('model', 'unknown'),
                'prompt_id': snippet.get('prompt_id', 'unknown'),
                'scanner': f['scanner'],
                'cwe_id': f['cwe_id'],
                'raw_severity': f['raw_severity'],
                'mapped_ordinal_rank': 0,
                'finding_text': f['finding_text'],
                'line_number': f.get('line_number', 0)
            })
            finding_id_counter += 1

    # Save to CSV
    if final_findings:
        import csv
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ['finding_id', 'snippet_id', 'model', 'prompt_id', 'scanner', 'cwe_id', 'raw_severity', 'mapped_ordinal_rank', 'finding_text', 'line_number']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_findings)
        
        logger.info(f"Saved {len(final_findings)} findings to {output_path}")
    else:
        logger.warning("No findings generated.")
        # Create empty file with headers
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

def main():
    """Main entry point for analysis."""
    # Load generated snippets
    snippets_path = Path(config.DATA_DIR) / 'generated' / 'snippets.csv'
    if not snippets_path.exists():
        logger.error(f"Snippets file not found: {snippets_path}. Run generate.py first.")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(snippets_path)
    snippets_list = df.to_dict('records')

    output_path = Path(config.DATA_DIR) / 'findings' / 'raw_findings.csv'
    
    analyze_snippets(snippets_list, str(output_path))
    logger.info("Analysis complete.")

if __name__ == '__main__':
    main()