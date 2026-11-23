import pytest
import os
import json
import tempfile
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.generators.logic_generator import main as logic_main
from src.generators.grid_generator import main as grid_main
from src.generators.test_generator import main as test_main
from src.generators.data_writer import main as writer_main
from src.analysis.validate_dataset import main as validate_main

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_pipeline_generation(temp_data_dir):
    """Test that the pipeline generates all required files."""
    # T011: Logic
    logic_path = os.path.join(temp_data_dir, 'generated_proofs.json')
    logic_main(type('Args', (), {'count': 10, 'seed': 42, 'output': logic_path})())
    assert os.path.exists(logic_path)
    with open(logic_path) as f:
        proofs = json.load(f)
    assert len(proofs) > 0

    # T012: Grid
    grid_path = os.path.join(temp_data_dir, 'generated_grids.json')
    grid_main(type('Args', (), {'count': 5, 'seed': 43, 'output': grid_path})())
    assert os.path.exists(grid_path)
    with open(grid_path) as f:
        grids = json.load(f)
    assert len(grids) > 0

    # T013: Test Instances
    test_path = os.path.join(temp_data_dir, 'test_instances.json')
    test_main(type('Args', (), {'seed': 44, 'output': test_path})())
    assert os.path.exists(test_path)
    with open(test_path) as f:
        tests = json.load(f)
    assert len(tests) > 0

    # T014: Checksums
    checksum_path = os.path.join(temp_data_dir, 'checksums.json')
    writer_main(type('Args', (), {'files': [logic_path, grid_path, test_path], 'checksum_file': checksum_path})())
    assert os.path.exists(checksum_path)

    # T015b: Validation
    report_path = os.path.join(temp_data_dir, 'validation_report.json')
    validate_main(type('Args', (), {'proofs': logic_path, 'grids': grid_path, 'output': report_path})())
    assert os.path.exists(report_path)
    with open(report_path) as f:
        report = json.load(f)
    assert report['overall_valid'] is True