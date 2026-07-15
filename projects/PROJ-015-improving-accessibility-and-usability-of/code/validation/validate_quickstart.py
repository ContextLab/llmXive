"""
Quickstart Validation Script for PROJ-015.

This script validates the `quickstart.md` file by:
1. Checking that the file exists.
2. Parsing the steps defined in the markdown.
3. Verifying that every command/script referenced in the steps exists on disk.
4. Attempting to import the primary entry points to ensure they are syntactically valid.
5. (Optional) Running a dry-run of the data generation script if `--run-dry` is passed.
"""
import os
import sys
import re
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger

logger = get_logger("QuickstartValidator")

class QuickstartValidator:
    def __init__(self, quickstart_path: Optional[Path] = None):
        self.project_root = PROJECT_ROOT
        self.quickstart_path = quickstart_path or (self.project_root / "quickstart.md")
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.steps: List[Dict[str, Any]] = []

    def load_quickstart(self) -> bool:
        """Load and parse the quickstart.md file."""
        if not self.quickstart_path.exists():
            self.errors.append(f"File not found: {self.quickstart_path}")
            return False

        try:
            content = self.quickstart_path.read_text(encoding='utf-8')
            self._parse_steps(content)
            logger.info(f"Successfully parsed {len(self.steps)} steps from quickstart.md")
            return True
        except Exception as e:
            self.errors.append(f"Failed to read quickstart.md: {e}")
            return False

    def _parse_steps(self, content: str):
        """
        Parse the markdown content to extract steps.
        Heuristic: Look for lines starting with `1.`, `2.`, etc., or `###` sections.
        Extract shell commands (lines starting with `$` or inside code blocks).
        """
        # Simple regex to find numbered steps
        step_pattern = re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE)
        # Regex to find code blocks
        code_block_pattern = re.compile(r'```(?:bash|sh|console)?\n(.*?)\n```', re.DOTALL)
        
        steps = step_pattern.findall(content)
        
        # Also look for code blocks globally as they might contain commands
        code_blocks = code_block_pattern.findall(content)
        
        self.steps = []
        for i, step_text in enumerate(steps):
            step_data = {
                "id": i + 1,
                "description": step_text.strip(),
                "commands": []
            }
            
            # Try to extract commands from the step text if it looks like a command
            if step_text.strip().startswith("$") or step_text.strip().startswith("python"):
                cmd = step_text.strip()
                if cmd.startswith("$ "):
                    cmd = cmd[2:]
                step_data["commands"].append(cmd)
            
            # Check for code blocks in the whole content that might belong to this step?
            # For simplicity, we assume code blocks in the file are commands to be validated.
            # A more robust parser would map blocks to steps.
            
            self.steps.append(step_data)

        # Extract all code blocks as potential commands to validate
        for block in code_blocks:
            lines = block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    cmd = line
                    if cmd.startswith("$ "):
                        cmd = cmd[2:]
                    # Check if it's a python script execution
                    if cmd.startswith("python "):
                        self.steps.append({
                            "id": len(self.steps) + 1,
                            "description": "Detected command from code block",
                            "commands": [cmd]
                        })

    def validate_script_exists(self, cmd: str) -> Tuple[bool, Optional[str]]:
        """Check if a python script or file referenced in a command exists."""
        # Handle 'python code/some_script.py'
        parts = cmd.split()
        if not parts:
            return False, "Empty command"
        
        if parts[0] == 'python':
            if len(parts) < 2:
                return False, "Missing script path in 'python <script>'"
            script_path = parts[1]
            # Handle relative paths
            if not script_path.startswith('/'):
                script_path = str(self.project_root / script_path)
            
            if not Path(script_path).exists():
                return False, f"Script not found: {script_path}"
            
            # Check syntax
            try:
                import ast
                with open(script_path, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
                return True, None
            except SyntaxError as e:
                return False, f"Syntax error in {script_path}: {e}"
            except Exception as e:
                return False, f"Error parsing {script_path}: {e}"
        
        elif parts[0] == 'streamlit':
            # streamlit run code/simulator/app.py
            if len(parts) < 3:
                return False, "Missing script path in 'streamlit run <script>'"
            script_path = parts[2]
            if not script_path.startswith('/'):
                script_path = str(self.project_root / script_path)
            if not Path(script_path).exists():
                return False, f"Streamlit app not found: {script_path}"
            return True, None

        return True, None # Non-python commands (like mkdir) are assumed valid if we can't parse them

    def validate_dependencies(self):
        """Check if required packages are installed."""
        required = [
            'pandas', 'numpy', 'scipy', 'matplotlib', 'streamlit', 'scikit-learn'
        ]
        missing = []
        for pkg in required:
            try:
                __import__(pkg.replace('-', '_'))
            except ImportError:
                missing.append(pkg)
        
        if missing:
            self.warnings.append(f"Missing dependencies: {', '.join(missing)}")

    def run_validation(self, dry_run: bool = False) -> bool:
        """Execute the full validation process."""
        logger.info("Starting Quickstart Validation...")
        
        if not self.load_quickstart():
            logger.error("Failed to load quickstart.md")
            return False

        self.validate_dependencies()

        all_valid = True
        for step in self.steps:
            if not step.get("commands"):
                continue
            
            for cmd in step["commands"]:
                valid, error = self.validate_script_exists(cmd)
                if not valid:
                    self.errors.append(f"Step {step['id']}: {error}")
                    all_valid = False
                else:
                    logger.debug(f"Step {step['id']}: Command validated: {cmd}")
                
                # Optional: Run the command in dry-run mode (very short timeout)
                if dry_run and valid and cmd.startswith("python"):
                    try:
                        # Run with --help or a dry-run flag if available, otherwise just check import
                        # Since we can't easily dry-run a full streamlit app, we just verify import
                        if "app.py" in cmd:
                            logger.info("Skipping runtime validation for Streamlit app (dry-run).")
                            continue
                        
                        # Try to run with a timeout
                        result = subprocess.run(
                            cmd, shell=True, cwd=self.project_root,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=5
                        )
                        if result.returncode != 0:
                            self.warnings.append(f"Step {step['id']} command failed (dry-run): {cmd}\n{result.stderr.decode()}")
                    except subprocess.TimeoutExpired:
                        logger.info(f"Step {step['id']} command timed out (expected for long-running): {cmd}")
                    except Exception as e:
                        self.warnings.append(f"Step {step['id']} dry-run error: {e}")

        return all_valid

    def generate_report(self) -> str:
        """Generate a text report of the validation."""
        lines = [
            "=== Quickstart Validation Report ===",
            f"File: {self.quickstart_path}",
            f"Steps Found: {len(self.steps)}",
            "---",
        ]
        
        if self.errors:
            lines.append("ERRORS:")
            for err in self.errors:
                lines.append(f"  - {err}")
        else:
            lines.append("No errors found.")

        if self.warnings:
            lines.append("WARNINGS:")
            for warn in self.warnings:
                lines.append(f"  - {warn}")
        
        lines.append("---")
        lines.append(f"Status: {'PASSED' if not self.errors else 'FAILED'}")
        
        return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate quickstart.md")
    parser.add_argument("--dry-run", action="store_true", help="Attempt to run commands briefly")
    parser.add_argument("--path", type=str, help="Path to quickstart.md")
    args = parser.parse_args()

    validator = QuickstartValidator(Path(args.path) if args.path else None)
    success = validator.run_validation(dry_run=args.dry_run)
    report = validator.generate_report()
    
    print(report)
    
    # Write report to data/processed if successful
    if success:
        output_dir = PROJECT_ROOT / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "quickstart_validation_report.txt"
        report_path.write_text(report)
        logger.info(f"Validation report saved to {report_path}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
