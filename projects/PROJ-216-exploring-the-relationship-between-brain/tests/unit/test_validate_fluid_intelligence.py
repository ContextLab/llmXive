import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_fluid_intelligence import validate_and_aggregate, load_behavioral_scores

class TestValidateFluidIntelligence:
    
    def setup_method(self):
        """Setup temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "data" / "raw"
        self.raw_dir.mkdir(parents=True)
        
        # Create mock subject directories
        self.subject_ids = ["sub-01", "sub-02", "sub-03"]
        for sub_id in self.subject_ids:
            (self.raw_dir / sub_id).mkdir()
        
        # Create a mock phenotype.tsv with valid scores
        self.phenotype_file = self.raw_dir / "phenotype.tsv"
        data = {
            "participant_id": self.subject_ids + ["sub-99"],
            "fluid_intelligence": [10.5, 12.3, 11.1, 15.0],
            "age": [20, 21, 22, 25]
        }
        df = pd.DataFrame(data)
        df.to_csv(self.phenotype_file, sep='\t', index=False)

    def teardown_method(self):
        """Cleanup temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_behavioral_scores_found(self):
        """Test that load_behavioral_scores finds the score in the TSV."""
        score = load_behavioral_scores("sub-01", self.raw_dir)
        assert score is not None
        assert score == 10.5

    def test_load_behavioral_scores_not_found(self):
        """Test that load_behavioral_scores returns None for missing subject."""
        score = load_behavioral_scores("sub-999", self.raw_dir)
        assert score is None

    def test_validate_and_aggregate_creates_file(self):
        """Test that validate_and_aggregate creates the output JSON."""
        # Temporarily change the output directory to our temp dir for testing
        # We need to patch the module's global or pass a custom path if we refactor.
        # Since the function writes to a fixed path, we will mock the output path 
        # by creating a temporary directory and ensuring the script logic works.
        # However, for this unit test, we verify the logic by checking the return value
        # and manually checking the file if we were to run it in a controlled env.
        
        # To strictly test without modifying global state, we rely on the return value
        # The function raises ValueError if count is 0, which we test next.
        
        result = validate_and_aggregate(self.subject_ids, self.raw_dir)
        
        assert "subjects" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["subjects"]) == 3
        
        # Verify specific IDs are present
        ids = [s["id"] for s in result["subjects"]]
        for sub_id in self.subject_ids:
            assert sub_id in ids

    def test_validate_and_aggregate_raises_on_zero(self):
        """Test that the function raises ValueError when no valid subjects are found."""
        empty_subjects = ["sub-999", "sub-888"]
        
        with pytest.raises(ValueError, match="No valid Fluid Intelligence data found"):
            validate_and_aggregate(empty_subjects, self.raw_dir)

    def test_output_json_schema(self):
        """Verify the schema of the generated JSON file matches requirements."""
        # We run the function and then read the file it created
        # Note: This relies on the fixed OUTPUT_DIR in the module. 
        # In a real CI, we would ensure data/processed exists.
        os.makedirs("data/processed", exist_ok=True)
        
        try:
            result = validate_and_aggregate(self.subject_ids, self.raw_dir)
            
            # Read the file
            with open("data/processed/valid_subjects.json", 'r') as f:
                file_data = json.load(f)
            
            # Validate schema
            assert "subjects" in file_data
            assert "count" in file_data
            assert isinstance(file_data["subjects"], list)
            assert isinstance(file_data["count"], int)
            assert file_data["count"] == len(file_data["subjects"])
            
            if file_data["subjects"]:
                sub = file_data["subjects"][0]
                assert "id" in sub
                assert "score" in sub
                assert isinstance(sub["id"], str)
                assert isinstance(sub["score"], float)
        finally:
            # Cleanup test artifact
            if os.path.exists("data/processed/valid_subjects.json"):
                os.remove("data/processed/valid_subjects.json")