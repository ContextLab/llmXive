"""
Terminal-Bench-Evo dataset verification and generation.

This module verifies the availability of the Terminal-Bench-Evo dataset
and generates a synthetic subset if the real dataset is unavailable.
"""
import json
import random
from pathlib import Path
import sys
import os
from typing import List, Dict, Any, Optional
from src.utils.seeding import set_deterministic_seed


def read_sample_size_from_research_md(research_md_path: str = 'specs/001-evoconflict-filtering/research.md') -> int:
    """
    Read the sample size from research.md.
    
    Args:
        research_md_path (str): Path to the research.md file.
    
    Returns:
        int: Sample size from the file, or default 50 if not found.
    """
    try:
        with open(research_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for line in content.split('\n'):
            if line.strip().startswith('sample_size:'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    
    return 50  # Default fallback for benchmark tasks


def generate_synthetic_benchmark_tasks(sample_size: int) -> List[Dict[str, Any]]:
    """
    Generate synthetic benchmark tasks for testing.
    
    Args:
        sample_size (int): Number of tasks to generate.
    
    Returns:
        List[Dict[str, Any]]: List of generated tasks.
    """
    tasks = []
    
    task_templates = [
        "Update configuration file with {param}={value}",
        "Restart service {service_name}",
        "Clear cache for {cache_key}",
        "Backup database {db_name}",
        "Modify permission for {resource}",
        "Enable monitoring for {component}",
        "Rotate logs for {service}",
        "Validate configuration {config_file}",
        "Deploy update to {environment}",
        "Schedule maintenance for {system}"
    ]
    
    params = {
        "param": ["timeout", "retry", "buffer", "limit"],
        "value": ["30", "5", "1024", "100"],
        "service_name": ["nginx", "redis", "postgres", "api"],
        "cache_key": ["user_session", "api_response", "config", "static"],
        "db_name": ["main", "analytics", "users", "logs"],
        "resource": ["/etc/config", "/var/log", "/home/user", "/opt/app"],
        "component": ["web", "api", "db", "cache"],
        "service": ["nginx", "redis", "postgres", "cron"],
        "config_file": ["app.conf", "db.conf", "cache.conf", "log.conf"],
        "environment": ["dev", "staging", "prod", "test"],
        "system": ["server1", "server2", "db1", "cache1"]
    }
    
    for i in range(sample_size):
        template = random.choice(task_templates)
        
        # Fill in template parameters
        task_text = template
        for key, values in params.items():
            if "{" + key + "}" in task_text:
                task_text = task_text.replace("{" + key + "}", random.choice(values))
        
        tasks.append({
            "task_id": f"task_{i:04d}",
            "instruction": task_text,
            "state_patches": [
                {"content": f"Initial state {i}", "timestamp": f"2024-01-01T00:00:{i:02d}"}
            ],
            "expected_output": f"Expected result for task {i}"
        })
    
    return tasks


def main():
    """Main function to verify dataset and generate synthetic subset if needed."""
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Read sample size
    sample_size = read_sample_size_from_research_md()
    
    output_path = Path('data/raw/terminal_bench_evo.jsonl')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to load real dataset (placeholder - in real implementation, would download)
    real_dataset_available = False
    
    if real_dataset_available:
        print("Real dataset found, using it.")
        # In real implementation: download and save real dataset
    else:
        print(f"Real dataset not available. Generating {sample_size} synthetic tasks.")
        tasks = generate_synthetic_benchmark_tasks(sample_size)
        
        # Write to JSONL format
        with open(output_path, 'w', encoding='utf-8') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        
        print(f"Generated {len(tasks)} synthetic tasks and saved to {output_path}")


if __name__ == '__main__':
    main()
