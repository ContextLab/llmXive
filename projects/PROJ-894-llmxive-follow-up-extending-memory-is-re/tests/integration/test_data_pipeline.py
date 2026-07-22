"""
Integration tests for the data loading pipeline.
"""

import pytest
import json
from pathlib import Path
import tempfile
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import (
    ensure_output_dirs,
    generate_noisy_graphs,
    save_noisy_graphs,
    save_raw_data
)

def test_full_data_pipeline():
    """Test the complete data pipeline from raw data to noisy graphs."""
    # Create sample raw data
    raw_tasks = [
        {
            "task_id": "integration_test_1",
            "question": "What is the relationship between X and Y?",
            "context": "X is connected to Y. Y is also connected to Z. X influences Y significantly.",
            "answer": "X is connected to Y"
        },
        {
            "task_id": "integration_test_2",
            "question": "Who is the author?",
            "context": "Alice wrote the book. Bob edited it. The book was published by Charlie.",
            "answer": "Alice"
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Setup directories
        raw_dir = tmp_path / "raw"
        graphs_dir = tmp_path / "graphs"
        raw_dir.mkdir()
        graphs_dir.mkdir()
        
        # Temporarily override directories
        import data_loader
        original_raw_dir = data_loader.RAW_DATA_DIR
        original_graphs_dir = data_loader.GRAPHS_DIR
        data_loader.RAW_DATA_DIR = raw_dir
        data_loader.GRAPHS_DIR = graphs_dir
        
        try:
            # Step 1: Save raw data
            save_raw_data(raw_tasks, "integration_test.json")
            
            # Verify raw data saved
            raw_file = raw_dir / "integration_test.json"
            assert raw_file.exists()
            
            with open(raw_file, 'r') as f:
                loaded_raw = json.load(f)
            assert len(loaded_raw) == len(raw_tasks)
            
            # Step 2: Generate noisy graphs
            noisy_tasks = generate_noisy_graphs(
                raw_tasks,
                noise_proportion=0.15,
                seed=999
            )
            
            # Verify noisy tasks
            assert len(noisy_tasks) == len(raw_tasks)
            for task in noisy_tasks:
                assert task["noisy_graph"] is not None
                assert task["original_graph"] is not None
            
            # Step 3: Save noisy graphs
            save_noisy_graphs(noisy_tasks, "integration_noisy.json")
            
            # Verify noisy graphs saved
            noisy_file = graphs_dir / "integration_noisy.json"
            assert noisy_file.exists()
            
            with open(noisy_file, 'r') as f:
                loaded_noisy = json.load(f)
            assert len(loaded_noisy) == len(noisy_tasks)
            
            # Verify data integrity
            assert loaded_noisy[0]["task_id"] == "integration_test_1"
            assert loaded_noisy[0]["noise_proportion"] == 0.15
            
        finally:
            # Restore original directories
            data_loader.RAW_DATA_DIR = original_raw_dir
            data_loader.GRAPHS_DIR = original_graphs_dir