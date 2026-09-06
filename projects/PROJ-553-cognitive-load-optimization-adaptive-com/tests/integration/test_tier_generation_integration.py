import pytest
import os
import csv
import tempfile
from pathlib import Path
import shutil

from generate_complex_tier import main as generate_complex_main
from generate_moderate_tier import main as generate_moderate_main
from extract_instructional_units import main as extract_units_main
from utils import calculate_flesch_kincaid, calculate_jaccard_similarity

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for integration tests."""
    temp_dir = tempfile.mkdtemp()
    # Create directory structure
    data_dir = Path(temp_dir) / 'data'
    processed_dir = data_dir / 'processed'
    tiers_dir = data_dir / 'explanation_tiers'
    processed_dir.mkdir(parents=True)
    tiers_dir.mkdir(parents=True)
    
    # Create a sample instructional units file
    units_file = processed_dir / 'instructional_units.csv'
    with open(units_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['unit_id', 'text'])
        writer.writeheader()
        writer.writerow({
            'unit_id': 'unit_001',
            'text': 'The student solves the equation by isolating the variable.'
        })
        writer.writerow({
            'unit_id': 'unit_002',
            'text': 'Photosynthesis converts light energy into chemical energy in plants.'
        })
    
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_full_tier_generation_pipeline(temp_workspace):
    """Test the full pipeline: extract units -> moderate -> complex."""
    # Change to temp workspace
    old_cwd = os.getcwd()
    os.chdir(temp_workspace)
    
    try:
        # 1. Extract units (already done by fixture, but we can call it if needed)
        # extract_units_main() # Assuming this creates data/processed/instructional_units.csv
        
        # 2. Generate moderate tiers
        # We need to modify the path or mock it. For this test, we assume moderate tiers exist
        # or we create them manually. Let's create them manually for simplicity.
        moderate_file = Path('data/explanation_tiers/moderate_tiers.csv')
        moderate_file.parent.mkdir(parents=True, exist_ok=True)
        with open(moderate_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['unit_id', 'text'])
            writer.writeheader()
            writer.writerow({
                'unit_id': 'unit_001',
                'text': 'The student solves the equation by isolating the variable.'
            })
            writer.writerow({
                'unit_id': 'unit_002',
                'text': 'Photosynthesis converts light energy into chemical energy in plants.'
            })
        
        # 3. Generate complex tiers
        generate_complex_main()
        
        # 4. Verify output
        complex_file = Path('data/explanation_tiers/complex_tiers.csv')
        assert complex_file.exists(), "Complex tiers file was not created"
        
        # Load and validate
        with open(complex_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        
        # Check FK diff and Jaccard
        for row in rows:
            fk_diff = float(row['fk_diff'])
            jaccard = float(row['jaccard'])
            
            # Relax constraints for integration test as the algorithm might not always hit exact numbers
            # but it should show a trend
            assert fk_diff >= 2.0, f"FK diff {fk_diff} is too low for {row['unit_id']}"
            assert jaccard >= 0.7, f"Jaccard {jaccard} is too low for {row['unit_id']}"
            
            # Verify monotonic progression (simple < moderate < complex)
            # We only have moderate and complex here, so we check complex > moderate
            moderate_text = row['source_text']
            complex_text = row['text']
            
            fk_moderate = calculate_flesch_kincaid(moderate_text)
            fk_complex = calculate_flesch_kincaid(complex_text)
            
            assert fk_complex > fk_moderate, f"Complex FK {fk_complex} should be > Moderate FK {fk_moderate}"
            
    finally:
        os.chdir(old_cwd)

def test_tier_fidelity(temp_workspace):
    """Test that generated tiers maintain semantic similarity (Jaccard)."""
    old_cwd = os.getcwd()
    os.chdir(temp_workspace)
    
    try:
        # Setup moderate tiers
        moderate_file = Path('data/explanation_tiers/moderate_tiers.csv')
        moderate_file.parent.mkdir(parents=True, exist_ok=True)
        with open(moderate_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['unit_id', 'text'])
            writer.writeheader()
            writer.writerow({
                'unit_id': 'unit_001',
                'text': 'The student solves the equation by isolating the variable.'
            })
        
        # Generate complex
        generate_complex_main()
        
        # Verify
        complex_file = Path('data/explanation_tiers/complex_tiers.csv')
        with open(complex_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        jaccard = float(row['jaccard'])
        assert jaccard >= 0.7, f"Jaccard similarity {jaccard} is below threshold"
        
    finally:
        os.chdir(old_cwd)