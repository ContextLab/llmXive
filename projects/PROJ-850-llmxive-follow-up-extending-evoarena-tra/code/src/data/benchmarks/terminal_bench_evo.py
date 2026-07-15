import json
import random
from pathlib import Path
import sys
import os
from typing import List, Dict, Any, Optional
import numpy as np
import torch

# Import seeding utility
try:
    from src.utils.seeding import set_deterministic_seed
except ImportError:
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from utils.seeding import set_deterministic_seed

# Set seed at module load time
set_deterministic_seed(42)

from src.data.generators.power_analysis import update_research_md

def read_sample_size_from_research_md(research_md_path: Path) -> int:
    """Read sample size from research.md, fallback to 50 if not found."""
    if not research_md_path.exists():
        return 50
    
    content = research_md_path.read_text()
    for line in content.split('\n'):
        if line.strip().startswith("sample_size:"):
            try:
                return int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                return 50
    return 50

def generate_synthetic_benchmark_tasks(n_tasks: int) -> List[Dict[str, Any]]:
    """Generate synthetic benchmark tasks for Terminal-Bench-Evo."""
    tasks = []
    
    task_templates = [
        {
            "description": "Update the user's credit balance to a new value.",
            "command": "update_credits",
            "expected_state": "credits_updated"
        },
        {
            "description": "Change the system version to a specific release.",
            "command": "update_version",
            "expected_state": "version_changed"
        },
        {
            "description": "Toggle the database connection status.",
            "command": "toggle_db",
            "expected_state": "db_status_changed"
        },
        {
            "description": "Record the time of the last user login.",
            "command": "log_login",
            "expected_state": "login_logged"
        },
        {
            "description": "Adjust the temperature setting.",
            "command": "set_temperature",
            "expected_state": "temp_updated"
        }
    ]
    
    for i in range(n_tasks):
        template = random.choice(task_templates)
        tasks.append({
            "task_id": f"evo_{i:04d}",
            "description": template["description"],
            "command": template["command"],
            "expected_state": template["expected_state"],
            "initial_state": "system_ready",
            "difficulty": random.choice(["easy", "medium", "hard"])
        })
    
    return tasks

def main():
    """Main entry point for Terminal-Bench-Evo dataset verification/generation."""
    project_root = Path(__file__).parent.parent.parent.parent
    research_md_path = project_root / "specs" / "001-evoconflict-filtering" / "research.md"
    output_path = project_root / "data" / "raw" / "terminal_bench_evo.jsonl"
    
    # Read sample size
    n_tasks = read_sample_size_from_research_md(research_md_path)
    
    print(f"Generating {n_tasks} synthetic benchmark tasks...")
    tasks = generate_synthetic_benchmark_tasks(n_tasks)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSONL
    with open(output_path, 'w') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    
    print(f"Generated dataset saved to {output_path}")

if __name__ == "__main__":
    main()
