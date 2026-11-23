"""
Helper script to simulate the buffer creation for T016a if T014/T015 
do not write to the expected buffer file in the current run context.
In a real pipeline, T014/T015 would write to this buffer.
This script is for testing T016a's atomic write logic with real data structure.
"""
import csv
import os
from pathlib import Path

def create_sample_buffer():
    """Creates a sample buffer file for testing T016a."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    buffer_path = "data/processed/generation_buffer.csv"
    
    # Sample data structure matching HumanEval generation
    samples = [
        {
            "task_id": "HumanEval/0",
            "style": "pep8",
            "code": "def test():\n    return 1",
            "pass_status": "True"
        },
        {
            "task_id": "HumanEval/0",
            "style": "minified",
            "code": "def test():return 1",
            "pass_status": "True"
        },
        {
            "task_id": "HumanEval/1",
            "style": "pep8",
            "code": "def add(a,b):\n    return a+b",
            "pass_status": "False"
        }
    ]
    
    with open(buffer_path, 'w', newline='') as f:
        fieldnames = ["task_id", "style", "code", "pass_status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)
    
    print(f"Created buffer at {buffer_path} with {len(samples)} samples.")

if __name__ == "__main__":
    create_sample_buffer()
