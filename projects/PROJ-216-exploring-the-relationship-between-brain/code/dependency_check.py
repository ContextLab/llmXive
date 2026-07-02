"""
System-level dependency check script for FSL and AFNI availability.

This script verifies that the required neuroimaging software (FSL and AFNI)
are installed and accessible in the system PATH. It is a prerequisite for
the preprocessing pipeline (T015).

Outputs:
- Prints status to stdout
- Writes a JSON report to data/processed/dependency_check.json
- Exits with code 0 if all checks pass, 1 otherwise.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure the data/processed directory exists
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "dependency_check.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_TOOLS = {
    "FSL": {
        "commands": ["fslver", "fslmaths", "fslstats"],
        "env_vars": ["FSLDIR"],
        "description": "FSL (FMRIB Software Library)"
    },
    "AFNI": {
        "commands": ["3dcalc", "3dUnifize", "3dTshift"],
        "env_vars": ["AFNI_HOME"],
        "description": "AFNI (Analysis of Functional NeuroImages)"
    }
}

def run_command(cmd: list[str]) -> tuple[bool, str]:
    """
    Run a system command and return (success, output_or_error).
    """
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out: {cmd[0]}"
    except Exception as e:
        return False, str(e)

def check_tool_availability(tool_name: str, config: dict) -> dict:
    """
    Check if a tool and its dependencies are available.
    Returns a status dictionary.
    """
    status = {
        "name": tool_name,
        "description": config["description"],
        "installed": False,
        "commands_found": [],
        "commands_missing": [],
        "env_vars_found": [],
        "env_vars_missing": [],
        "details": []
    }

    # Check environment variables
    for env_var in config["env_vars"]:
        if env_var in os.environ:
            status["env_vars_found"].append(env_var)
            status["details"].append(f"Env var {env_var} found: {os.environ[env_var]}")
        else:
            status["env_vars_missing"].append(env_var)
            status["details"].append(f"Env var {env_var} NOT found")

    # Check commands
    for cmd in config["commands"]:
        success, output = run_command([cmd, "--help"]) if "--help" not in cmd else run_command([cmd, "-h"])
        # Fallback for tools that might not support --help/-h gracefully, try version or just existence
        if not success:
            # Try simple existence check (which/where)
            check_success, check_output = run_command(["which", cmd])
            if not check_success:
                check_success, check_output = run_command(["where", cmd]) if sys.platform == "win32" else (False, "")
            
            if check_success:
                status["commands_found"].append(cmd)
                status["details"].append(f"Command {cmd} found at: {check_output}")
            else:
                status["commands_missing"].append(cmd)
                status["details"].append(f"Command {cmd} NOT found in PATH")
        else:
            status["commands_found"].append(cmd)
            status["details"].append(f"Command {cmd} executed successfully")

    # Determine overall installation status
    # We require at least one env var and one command, or just the commands if env vars are optional
    if status["commands_found"]:
        status["installed"] = True
    
    return status

def main():
    print("Starting system dependency check for FSL and AFNI...")
    results = {}
    all_passed = True

    for tool_name, config in REQUIRED_TOOLS.items():
        print(f"\nChecking {tool_name}...")
        status = check_tool_availability(tool_name, config)
        results[tool_name] = status

        if status["installed"]:
            print(f"  [OK] {tool_name} is available.")
            print(f"       Found commands: {', '.join(status['commands_found'])}")
        else:
            print(f"  [FAIL] {tool_name} is NOT available or incomplete.")
            if status["commands_missing"]:
                print(f"       Missing commands: {', '.join(status['commands_missing'])}")
            if status["env_vars_missing"]:
                print(f"       Missing env vars: {', '.join(status['env_vars_missing'])}")
            all_passed = False

    # Write JSON report
    report = {
        "status": "passed" if all_passed else "failed",
        "timestamp": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip() if sys.platform != "win32" else "N/A",
        "tools": results
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport written to: {OUTPUT_FILE}")

    if not all_passed:
        print("\n⚠️  CRITICAL: One or more required dependencies are missing.")
        print("    The preprocessing pipeline (T015) cannot run without FSL/AFNI.")
        print("    Please install the missing software or configure your environment.")
        sys.exit(1)
    else:
        print("\n✅ All dependencies verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()