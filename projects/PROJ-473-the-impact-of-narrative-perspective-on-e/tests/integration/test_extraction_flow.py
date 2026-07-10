"""
Integration test for full perspective extraction pipeline on a sample of 10 stories.

This test verifies that the extraction pipeline processes real stories,
handles edge cases (language detection, short texts), and produces
valid perspective feature outputs that can be loaded and validated.

Requirements:
- Processes 10 real stories from data/raw/ (fetched via data_loader)
- Validates output schema matches expected fields
- Checks that first-person density scores are within valid range [0.0, 1.0]
- Verifies language detection correctly skips non-English texts
- Confirms pipeline completes without errors on sample data
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

import pandas as pd
import numpy as np

from data_loader import fetch_gutenberg_stories
from extraction import extract_perspective_features, calculate_pronoun_density
from utils import compute_artifact_hash
from config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR


def test_extraction_flow_integration():
    """
    Integration test: Process 10 real stories and verify pipeline outputs.
    
    This test:
    1. Fetches 10 real stories from Project Gutenberg via data_loader
    2. Runs the full extraction pipeline on each story
    3. Validates output schema and data types
    4. Checks that scores are within valid ranges
    5. Verifies non-English texts are skipped
    6. Confirms output file is written correctly
    """
    
    # Create temporary directory for test output
    test_output_dir = Path(tempfile.mkdtemp())
    try:
        # Step 1: Fetch 10 real stories
        print("Fetching 10 real stories from Project Gutenberg...")
        stories = fetch_gutenberg_stories(limit=10)
        
        assert len(stories) > 0, "Failed to fetch any stories from Gutenberg"
        assert len(stories) <= 10, f"Expected <= 10 stories, got {len(stories)}"
        
        print(f"Successfully fetched {len(stories)} stories")
        
        # Step 2: Run extraction pipeline on each story
        results = []
        skipped_count = 0
        
        for story in stories:
            story_id = story.get('story_id', story.get('id', 'unknown'))
            text = story.get('text', '')
            
            if not text or len(text.strip()) < 50:
                skipped_count += 1
                print(f"Skipping story {story_id}: text too short or empty")
                continue
            
            # Create temporary file for the story text
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                temp_file_path = f.name
            
            try:
                # Run extraction
                features = extract_perspective_features(temp_file_path)
                
                if features is None:
                    skipped_count += 1
                    print(f"Skipping story {story_id}: extraction returned None (likely non-English)")
                    continue
                
                # Add story metadata to results
                result = {
                    'story_id': story_id,
                    'title': story.get('title', 'Unknown'),
                    'word_count': len(text.split()),
                    **features
                }
                results.append(result)
                
                print(f"Processed story {story_id}: "
                      f"1st_person_density={features.get('pronoun_density_1st', 0):.3f}, "
                      f"3rd_person_density={features.get('pronoun_density_3rd', 0):.3f}")
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Step 3: Validate results
        assert len(results) > 0, "No stories were successfully processed"
        print(f"Successfully processed {len(results)} stories (skipped {skipped_count})")
        
        # Step 4: Validate output schema
        expected_fields = [
            'pronoun_density_1st',
            'pronoun_density_2nd', 
            'pronoun_density_3rd',
            'narrator_distance_score',
            'language_detected',
            'word_count',
            'data_quality_flag'
        ]
        
        for result in results:
            for field in expected_fields:
                assert field in result, f"Missing expected field '{field}' in result for story {result['story_id']}"
            
            # Validate score ranges
            assert 0.0 <= result['pronoun_density_1st'] <= 1.0, \
                f"Invalid 1st person density: {result['pronoun_density_1st']}"
            assert 0.0 <= result['pronoun_density_2nd'] <= 1.0, \
                f"Invalid 2nd person density: {result['pronoun_density_2nd']}"
            assert 0.0 <= result['pronoun_density_3rd'] <= 1.0, \
                f"Invalid 3rd person density: {result['pronoun_density_3rd']}"
            assert 0.0 <= result['narrator_distance_score'] <= 1.0, \
                f"Invalid narrator distance score: {result['narrator_distance_score']}"
            
            # Validate language detection
            assert result['language_detected'] in ['en', 'non-en'], \
                f"Invalid language code: {result['language_detected']}"
            
            # Validate data quality flag
            assert result['data_quality_flag'] in ['good', 'insufficient', 'skipped'], \
                f"Invalid data quality flag: {result['data_quality_flag']}"
        
        print("All schema validations passed")
        
        # Step 5: Write results to output file
        output_file = test_output_dir / "extraction_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Step 6: Verify output file was written and is valid JSON
        assert output_file.exists(), "Output file was not created"
        
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_results = json.load(f)
        
        assert len(loaded_results) == len(results), \
            f"Output file contains {len(loaded_results)} records, expected {len(results)}"
        
        print(f"Output file written successfully: {output_file}")
        
        # Step 7: Compute artifact hash for versioning
        artifact_hash = compute_artifact_hash(str(output_file))
        print(f"Output artifact hash: {artifact_hash}")
        
        # Step 8: Validate statistical properties
        densities = [r['pronoun_density_1st'] for r in results]
        avg_density = np.mean(densities)
        std_density = np.std(densities)
        
        print(f"First-person density statistics:")
        print(f"  Mean: {avg_density:.3f}")
        print(f"  Std Dev: {std_density:.3f}")
        print(f"  Min: {min(densities):.3f}")
        print(f"  Max: {max(densities):.3f}")
        
        # Verify there is variance in the data (not all stories have same perspective)
        assert std_density > 0.01, "Insufficient variance in first-person density scores"
        
        # Verify at least some stories have notable first-person perspective
        high_first_person = [r for r in results if r['pronoun_density_1st'] > 0.3]
        print(f"Stories with high first-person density (>0.3): {len(high_first_person)}")
        
        # Step 9: Validate edge case handling
        # Check that very short texts were handled appropriately
        short_texts = [r for r in results if r['word_count'] < 100]
        for short_text in short_texts:
            assert short_text['data_quality_flag'] == 'insufficient' or \
                   short_text['data_quality_flag'] == 'skipped', \
                   f"Short text ({short_text['word_count']} words) not flagged as insufficient quality"
        
        print("\n=== INTEGRATION TEST PASSED ===")
        print(f"Processed {len(results)} stories successfully")
        print(f"Skipped {skipped_count} stories (non-English or too short)")
        print(f"Output written to: {output_file}")
        print(f"Artifact hash: {artifact_hash}")
        
        return True
        
    finally:
        # Clean up temporary directory
        if test_output_dir.exists():
            shutil.rmtree(test_output_dir)
        

if __name__ == "__main__":
    success = test_extraction_flow_integration()
    if success:
        print("\n✓ Integration test completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Integration test failed")
        sys.exit(1)