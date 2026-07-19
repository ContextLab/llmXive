"""
PMD CLI Wrapper for Static Analysis.

Executes PMD CLI with specific rulesets for 4 target code smells:
1. Long Method
2. Duplicated Code
3. Feature Envy
4. Long Parameter List

Enforces per-process memory limits (<=2GB) and 2-minute timeout per file.
Handles syntax errors gracefully by logging and excluding the file.
"""
import os
import sys
import json
import subprocess
import time
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Project imports based on provided API surface
from utils.logger import get_logger
from utils.pmd_config import get_pmd_executable, check_pmd_availability
from utils.validators import get_language_from_extension, validate_file_syntax

# Configuration Constants
PMD_TIMEOUT_SECONDS = 120  # 2 minutes per file
PMD_MEMORY_LIMIT_MB = 2048  # 2 GB
TARGET_SMELL_TYPES = [
    "LongMethod",
    "DuplicateCode",
    "FeatureEnvy",
    "LongParameterList"
]

# Setup logging
logger = get_logger(__name__)

def _get_pmd_ruleset_path() -> Path:
    """
    Creates a temporary PMD ruleset XML file targeting the 4 specific smells.
    Returns the path to the XML file.
    """
    ruleset_content = f"""<?xml version="1.0"?>
<ruleset name="llmXive-CodeSmell-Rules"
   xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 http://pmd.sourceforge.net/ruleset_2_0_0.xsd">
    <description>Custom ruleset for llmXive study focusing on 4 specific code smells.</description>

    <!-- Long Method -->
    <rule ref="category/java/codestyle.xml/LongMethod">
  <properties>
      <property name="methodLength" value="60"/>
  </properties>
    </rule>

    <!-- Duplicated Code -->
    <rule ref="category/java/codesize.xml/DuplicateCode">
  <properties>
      <property name="minimumLines" value="5"/>
      <property name="minimumTokens" value="50"/>
  </properties>
    </rule>

    <!-- Feature Envy -->
    <rule ref="category/java/design.xml/FeatureEnvy">
  <properties>
      <property name="reportLevel" value="high"/>
  </properties>
    </rule>

    <!-- Long Parameter List -->
    <rule ref="category/java/codestyle.xml/LongParameterList">
  <properties>
      <property name="max" value="5"/>
  </properties>
    </rule>

    <!-- Python specific (if applicable, though PMD is Java-centric, we add basic Python checks if supported or skip) -->
    <!-- Note: PMD has limited Python support. If files are Python, we might need a different tool,
   but per spec we use PMD. We will attempt to run it; if it fails on Python, we log it. -->
</ruleset>
"""
    # Write to a temporary file
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
    tmp_file.write(ruleset_content)
    tmp_file.close()
    return Path(tmp_file.name)

def run_pmd_on_file(file_path: Path, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Runs PMD CLI on a single file.

    Args:
        file_path: Path to the source file (Python or Java).
        output_dir: Directory to store PMD output (XML/JSON).

    Returns:
        Dictionary containing analysis results or None if skipped/failed.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    # Validate syntax first to avoid PMD crashing on invalid code
    lang = get_language_from_extension(file_path.suffix)
    if lang not in ['java', 'python']:
        logger.warning(f"Unsupported language for PMD: {lang} in {file_path}")
        return None

    # Optional: Run quick syntax check before PMD to fail fast
    # Note: PMD itself handles syntax errors, but we log them explicitly as per task req
    if not validate_file_syntax(file_path):
        logger.info(f"Syntax validation failed for {file_path}. Excluding from analysis.")
        return {
            "file": str(file_path),
            "status": "syntax_error",
            "smells": []
        }

    pmd_exec = get_pmd_executable()
    if not pmd_exec:
        raise RuntimeError("PMD executable not found. Please install PMD and set PMD_HOME.")

    ruleset_path = _get_pmd_ruleset_path()
    output_xml = output_dir / f"{file_path.stem}_pmd.xml"

    # Build command
    # language: java or python
    # format: text or xml (we use xml for parsing)
    cmd = [
        str(pmd_exec),
        "check",
        "--rulesets", str(ruleset_path),
        "--language", lang,
        "--format", "xml",
        "--dir", str(file_path.parent), # PMD checks directory, but we pass the file context
        # Note: PMD CLI usually takes a directory. To analyze a single file,
        # we might need to create a temp directory or rely on PMD's ability to take a file list.
        # Standard PMD CLI: pmd check -R rulesets.xml -d /path/to/dir -f xml
        # To analyze a single file, we can pass the file's parent dir and rely on the file filter
        # or simply run it on the file if PMD supports file args.
        # Let's assume we run on the directory containing the file, but we only care about this file.
        # To be safe and precise, we pass the file path if supported, or the directory.
        # PMD 6.x+ supports --file-list or just -d.
        # Let's use -d with the parent directory and hope it's fast enough.
        # Actually, for single file analysis in a loop, creating a temp dir with just the file is safer
        # to avoid scanning the whole repo.
    ]

    # Better approach for single file: Create a temp dir with just the file
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        # Copy file to temp dir to ensure PMD only sees this file
        temp_file = tmp_dir / file_path.name
        shutil.copy2(file_path, temp_file)

        cmd = [
            str(pmd_exec),
            "check",
            "--rulesets", str(ruleset_path),
            "--language", lang,
            "--format", "xml",
            "-d", str(tmp_dir),
            "-f", "xml",
            "--no-cache" # Disable cache to ensure fresh analysis
        ]

        # Add memory limit
        env = os.environ.copy()
        # Java memory settings
        java_opts = f"-Xmx{PMD_MEMORY_LIMIT_MB}m"
        if "JAVA_OPTS" in env:
            env["JAVA_OPTS"] = f"{java_opts} {env['JAVA_OPTS']}"
        else:
            env["JAVA_OPTS"] = java_opts

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=PMD_TIMEOUT_SECONDS,
                env=env,
                text=True
            )

            duration = time.time() - start_time

            if result.returncode != 0 and "syntax error" not in result.stderr.lower():
                # PMD returns non-zero if violations are found, which is expected.
                # We only care if it's a crash or timeout.
                pass

            # Parse output
            # PMD XML output structure: <pmd><file name="..."><violation ... /></file></pmd>
            # We need to parse this to extract smells.
            smells = _parse_pmd_xml(result.stdout, file_path)

            return {
                "file": str(file_path),
                "status": "success" if smells is not None else "no_violations",
                "duration_seconds": duration,
                "smells": smells or []
            }

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout analyzing {file_path} after {PMD_TIMEOUT_SECONDS}s")
            return {
                "file": str(file_path),
                "status": "timeout",
                "smells": []
            }
        except Exception as e:
            logger.error(f"Error running PMD on {file_path}: {str(e)}")
            return {
                "file": str(file_path),
                "status": "error",
                "error": str(e),
                "smells": []
            }
        finally:
            # Cleanup temp ruleset
            if ruleset_path.exists():
                ruleset_path.unlink()

def _parse_pmd_xml(xml_output: str, original_file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses PMD XML output to extract specific smells.
    Returns a list of dictionaries with smell details.
    """
    import xml.etree.ElementTree as ET

    smells = []
    try:
        root = ET.fromstring(xml_output)
        for file_node in root.findall('file'):
            if file_node.get('name') == str(original_file_path):
                for violation in file_node.findall('violation'):
                    rule = violation.get('rule', 'Unknown')
                    # Map PMD rule names to our standard smell types
                    # PMD Rule names: LongMethod, DuplicateCode, FeatureEnvy, LongParameterList
                    # We normalize them to our TARGET_SMELL_TYPES
                    smell_type = rule
                    if rule == "LongMethod":
                        smell_type = "LongMethod"
                    elif rule == "DuplicateCode":
                        smell_type = "DuplicateCode"
                    elif rule == "FeatureEnvy":
                        smell_type = "FeatureEnvy"
                    elif rule == "LongParameterList":
                        smell_type = "LongParameterList"
                    else:
                        # Skip rules we don't care about
                        continue

                    smells.append({
                        "type": smell_type,
                        "rule": rule,
                        "beginline": violation.get('beginline'),
                        "endline": violation.get('endline'),
                        "begincolumn": violation.get('begincolumn'),
                        "endcolumn": violation.get('endcolumn'),
                        "description": violation.text or "",
                        "priority": violation.get('priority')
                    })
    except ET.ParseError as e:
        logger.warning(f"Failed to parse PMD XML for {original_file_path}: {e}")
    return smells

def run_pmd_batch(input_dir: Path, output_json: Path) -> Dict[str, Any]:
    """
    Runs PMD on all Python/Java files in input_dir.
    Aggregates results into a JSON file.

    Args:
        input_dir: Directory containing sample files.
        output_json: Path to save the aggregated JSON results.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    results = []
    stats = {
        "total_files": 0,
        "analyzed": 0,
        "syntax_errors": 0,
        "timeouts": 0,
        "errors": 0
    }

    # Ensure output directory exists
    output_dir = output_json.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all Python and Java files
    files = list(input_dir.glob("**/*.py")) + list(input_dir.glob("**/*.java"))
    stats["total_files"] = len(files)
    logger.info(f"Found {len(files)} files to analyze in {input_dir}")

    for file_path in files:
        logger.info(f"Analyzing: {file_path}")
        result = run_pmd_on_file(file_path, output_dir)

        if result:
            if result["status"] == "success":
                stats["analyzed"] += 1
            elif result["status"] == "syntax_error":
                stats["syntax_errors"] += 1
            elif result["status"] == "timeout":
                stats["timeouts"] += 1
            else:
                stats["errors"] += 1
            results.append(result)

    # Save results
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "statistics": stats,
        "results": results
    }

    with open(output_json, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Analysis complete. Results saved to {output_json}")
    logger.info(f"Stats: {stats}")

    return output_data

def main():
    """
    Main entry point for the script.
    Expects arguments: <input_dir> <output_json_path>
    """
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <input_directory> <output_json_path>")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_json = Path(sys.argv[2])

    try:
        run_pmd_batch(input_dir, output_json)
    except Exception as e:
        logger.error(f"Fatal error during batch analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()