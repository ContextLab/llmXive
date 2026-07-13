import os
import sys

def test_requirements_file_exists():
    """Test that requirements.txt exists in the project root."""
    # Assuming the test is run from the project root or tests/ directory
    # Check common locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt'),
        os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'),
        'requirements.txt'
    ]
    
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            found = True
            break
    
    assert found, "requirements.txt not found in expected locations"

def test_requirements_contains_mobilegym():
    """Test that requirements.txt contains mobilegym."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt'),
        os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'),
        'requirements.txt'
    ]
    
    req_file = None
    for path in possible_paths:
        if os.path.exists(path):
            req_file = path
            break
    
    assert req_file is not None, "requirements.txt not found"
    
    with open(req_file, 'r') as f:
        content = f.read().lower()
    
    assert 'mobilegym' in content, "mobilegym not found in requirements.txt"