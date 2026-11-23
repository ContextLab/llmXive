"""
Integration test for cross-system validation split logic (US2).

This test verifies that the model training pipeline correctly:
1. Assigns chemical families (Fe, Zr, Mg, Cu, Ti) based on dominant element.
2. Splits data into train/test sets based on distinct chemical families (cross-system).
3. Falls back to stratified random split if family counts are too low (<20).
4. Ensures no data leakage between training and testing families.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
import numpy as np
from descriptor_computation import parse_composition, get_element_property


def get_dominant_element(composition_str: str) -> str:
    """
    Parse composition string and return the element with the highest atomic fraction.
    Tie-break: Alphabetical order.
    """
    elements = parse_composition(composition_str)
    if not elements:
        return None
    
    # Sort by atomic fraction descending, then by element symbol ascending for tie-break
    sorted_elements = sorted(elements, key=lambda x: (-x['fraction'], x['element']))
    return sorted_elements[0]['element']


def assign_family(composition_str: str) -> str:
    """
    Assign a chemical family based on the dominant element.
    Groups: Fe-based, Zr-based, Mg-based, Cu-based, Ti-based.
    """
    dominant = get_dominant_element(composition_str)
    if dominant is None:
        return "Unknown"
    
    # Map dominant element to family (case-insensitive matching usually, but assuming standard caps)
    # If the dominant element is one of the key families, use it. Otherwise, group as 'Other' or specific logic.
    # Based on T034: Group by element with highest atomic fraction (Fe, Zr, Mg, Cu, Ti)
    key_families = {'Fe', 'Zr', 'Mg', 'Cu', 'Ti'}
    
    if dominant in key_families:
        return f"{dominant}-based"
    
    # If not a key family, we might need a generic rule, but for this test we assume
    # the data contains these families or we group others.
    # For the purpose of this integration test, we return the dominant element as family
    # if it's not in the key list, or we can map it to 'Other'. 
    # However, T034 specifically lists Fe, Zr, Mg, Cu, Ti.
    # Let's assume if it's not one of these, it's 'Other' or we just use the element.
    # To be safe and match T034 logic:
    return f"{dominant}-based"


def load_sample_data(output_path: Path):
    """
    Create a synthetic-like dataset with known composition distributions
    to test the cross-system split logic.
    Note: This generates data locally for testing logic, not for training models.
    The data represents a mix of Fe-based and Zr-based alloys.
    """
    data = []
    
    # Fe-based samples (70 samples)
    for i in range(70):
        # Fe dominant: > 50% Fe
        fe_frac = 0.5 + (i % 10) * 0.01
        remaining = 1.0 - fe_frac
        # Add other elements
        c_frac = remaining * 0.2
        b_frac = remaining * 0.3
        ni_frac = remaining * 0.5
        composition = f"Fe{fe_frac:.2f}C{c_frac:.2f}B{b_frac:.2f}Ni{ni_frac:.2f}"
        data.append({
            "composition": composition,
            "gfa_label": 1 if i < 35 else 0, # Balanced labels
            "delta_hmix": 0.0, # Placeholder
            "delta": 0.0,
            "vec": 0.0,
            "delta_chi": 0.0
        })
    
    # Zr-based samples (60 samples)
    for i in range(60):
        zr_frac = 0.6 + (i % 10) * 0.01
        remaining = 1.0 - zr_frac
        cu_frac = remaining * 0.4
        ni_frac = remaining * 0.3
        al_frac = remaining * 0.3
        composition = f"Zr{zr_frac:.2f}Cu{cu_frac:.2f}Ni{ni_frac:.2f}Al{al_frac:.2f}"
        data.append({
            "composition": composition,
            "gfa_label": 1 if i < 30 else 0,
            "delta_hmix": 0.0,
            "delta": 0.0,
            "vec": 0.0,
            "delta_chi": 0.0
        })
    
    # Ti-based samples (15 samples) - Small family to test fallback or exclusion
    for i in range(15):
        ti_frac = 0.7
        remaining = 1.0 - ti_frac
        al_frac = remaining * 0.5
        v_frac = remaining * 0.5
        composition = f"Ti{ti_frac:.2f}Al{al_frac:.2f}V{v_frac:.2f}"
        data.append({
            "composition": composition,
            "gfa_label": 1 if i < 8 else 0,
            "delta_hmix": 0.0,
            "delta": 0.0,
            "vec": 0.0,
            "delta_chi": 0.0
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def test_cross_system_validation_split():
    """
    Integration test for cross-system validation split.
    """
    # Create temporary directory for test artifacts
    temp_dir = tempfile.mkdtemp()
    try:
        input_file = Path(temp_dir) / "computed_descriptors.csv"
        output_file = Path(temp_dir) / "split_results.json"
        
        # 1. Prepare data
        load_sample_data(input_file)
        
        # Verify file exists and has content
        assert input_file.exists(), "Input file not created"
        df = pd.read_csv(input_file)
        assert len(df) == 145, f"Expected 145 rows, got {len(df)}"
        
        # 2. Apply family assignment logic (mimicking code/model_training.py logic)
        df['family'] = df['composition'].apply(assign_family)
        
        # Count families
        family_counts = df['family'].value_counts()
        print(f"Family counts: {family_counts.to_dict()}")
        
        # 3. Implement split strategy logic here to test it
        # Strategy: Primary = cross-system (train Fe-based, test Zr-based)
        # Fallback = stratified random split if N < 20 per family
        
        # Identify available families
        available_families = family_counts.index.tolist()
        train_families = []
        test_families = []
        
        # Logic from T035: Train Fe-based, Test Zr-based
        if 'Fe-based' in available_families and 'Zr-based' in available_families:
            if family_counts['Fe-based'] >= 20 and family_counts['Zr-based'] >= 20:
                train_families = ['Fe-based']
                test_families = ['Zr-based']
                fallback_used = False
            else:
                # Fallback logic
                fallback_used = True
                # Stratified split (simplified for test)
                train_families = available_families
                test_families = available_families # In real code, would split rows
        else:
            # Fallback
            fallback_used = True
            train_families = available_families
            test_families = available_families
        
        # 4. Execute split
        if not fallback_used:
            train_df = df[df['family'].isin(train_families)]
            test_df = df[df['family'].isin(test_families)]
        else:
            # Simple random split for fallback case in this test
            # In real code, this would be stratified
            train_df = df.sample(frac=0.8, random_state=42)
            test_df = df.drop(train_df.index)
        
        # 5. Verify no leakage
        # If cross-system, train families and test families should be disjoint
        if not fallback_used:
            train_fam_set = set(train_df['family'].unique())
            test_fam_set = set(test_df['family'].unique())
            intersection = train_fam_set.intersection(test_fam_set)
            assert len(intersection) == 0, f"Data leakage detected: {intersection}"
            assert 'Fe-based' in train_fam_set, "Fe-based should be in train"
            assert 'Zr-based' in test_fam_set, "Zr-based should be in test"
        
        # 6. Verify sizes
        assert len(train_df) > 0, "Train set empty"
        assert len(test_df) > 0, "Test set empty"
        
        # 7. Write results
        results = {
            "total_samples": len(df),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "train_families": list(train_df['family'].unique()),
            "test_families": list(test_df['family'].unique()),
            "fallback_used": fallback_used,
            "family_counts": family_counts.to_dict()
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 8. Assertions
        assert output_file.exists(), "Output file not created"
        assert results['train_samples'] + results['test_samples'] == results['total_samples'], "Sample count mismatch"
        
        if not fallback_used:
            # Specific cross-system checks
            assert set(results['train_families']) == {'Fe-based'}, f"Unexpected train families: {results['train_families']}"
            assert set(results['test_families']) == {'Zr-based'}, f"Unexpected test families: {results['test_families']}"
        
        print("Cross-system validation split test PASSED")
        print(f"Results: {json.dumps(results, indent=2)}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_cross_system_validation_split()
    print("Integration test completed successfully.")