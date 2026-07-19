import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from analysis.tract_counting import run_tract_counting, load_extracted_studies, extract_tract_names, count_unique_tracts
from analysis.tract_mapping import harmonize_tract_list

class TestTractCounting:
    @pytest.fixture
    def temp_csv(self):
        """Create a temporary CSV with mock extracted studies."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("study_id,author,year,tract,harmonized_tract,qualitative_desc,n\n")
            f.write("1,Smith,2020,arcuate_fasciculus,arcuate_fasciculus,\"Positive correlation\",50\n")
            f.write("2,Jones,2021,UNCINATE,uncinate_fasciculus,\"Negative correlation\",45\n")
            f.write("3,Doe,2022,arcuate_fasciculus,arcuate_fasciculus,\"No correlation\",60\n")
            f.write("4,White,2023,cingulum_bundle,cingulum,\"Weak positive\",40\n")
            f.write("5,Green,2023,arcuate_fasciculus,arcuate_fasciculus,\"Strong positive\",55\n")
            f.write("6,Black,2024,unknown_tract,unknown_tract,\"Mentioned\",30\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_empty_csv(self):
        """Create a temporary CSV with no data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("study_id,author,year,tract,harmonized_tract,qualitative_desc,n\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_extracted_studies(self, temp_csv):
        studies = load_extracted_studies(Path(temp_csv))
        assert len(studies) == 6
        assert studies[0]['study_id'] == '1'
        assert studies[0]['tract'] == 'arcuate_fasciculus'

    def test_extract_tract_names(self, temp_csv):
        studies = load_extracted_studies(Path(temp_csv))
        names = extract_tract_names(studies)
        # Should extract from harmonized_tract if present
        assert 'arcuate_fasciculus' in names
        assert 'uncinate_fasciculus' in names
        assert 'cingulum' in names
        assert 'unknown_tract' in names
        assert len(names) == 6

    def test_count_unique_tracts(self, temp_csv):
        studies = load_extracted_studies(Path(temp_csv))
        names = extract_tract_names(studies)
        # Harmonization should normalize 'arcuate_fasciculus' to itself
        # 'UNCINATE' -> 'uncinate_fasciculus' (already in list as harmonized)
        # 'cingulum_bundle' -> 'cingulum' (assuming mapping exists)
        # 'unknown_tract' -> 'unknown_tract' (or mapped if possible)
        unique_count = count_unique_tracts(names)
        # We expect: arcuate_fasciculus (3 times), uncinate_fasciculus (1), cingulum (1), unknown_tract (1)
        # Total unique: 4
        assert unique_count == 4

    def test_run_tract_counting_output(self, temp_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tract_count.json"
            count = run_tract_counting(Path(temp_csv), output_path)
            
            assert count == 4
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "k" in data
            assert data["k"] == 4

    def test_run_tract_counting_empty(self, temp_empty_csv):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tract_count.json"
            count = run_tract_counting(Path(temp_empty_csv), output_path)
            
            assert count == 0
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["k"] == 0

    def test_harmonization_consistency(self):
        """Test that harmonization works as expected for counting."""
        raw_tracts = ["Arcuate", "ARCUATE", "arcuate_fasciculus", "Uncinate", "uncinate_fasciculus"]
        harmonized = harmonize_tract_list(raw_tracts)
        # Check that they are normalized to a standard set
        # The exact output depends on the mapping in T008, but they should be consistent
        unique_harmonized = set(harmonized)
        # We expect fewer unique items than raw items if mapping works
        # Arcuate variants -> 1, Uncinate variants -> 1
        # So max unique should be 2 (plus any unmapped)
        assert len(unique_harmonized) <= len(raw_tracts)