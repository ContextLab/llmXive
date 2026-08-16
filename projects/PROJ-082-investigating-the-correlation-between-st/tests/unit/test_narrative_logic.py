"""
Unit tests for T015a: narrative_logic.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Ensure we can import from code/
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.narrative_logic import (
    load_methodology_config,
    load_extracted_studies,
    extract_themes,
    generate_themes_json,
    run_narrative_logic
)


def test_extract_themes_positive():
    """Test extraction of positive themes."""
    keywords = ["auditory", "reward"]
    sentiment_rules = {
        "positive": ["increased", "enhanced"],
        "negative": ["decreased"]
    }
    
    text = "Increased auditory connectivity to the reward pathway."
    themes = extract_themes(text, keywords, sentiment_rules)
    
    assert len(themes) > 0
    assert any(t["theme"] == "auditory" for t in themes)
    assert any(t["sentiment"] == "positive" for t in themes)


def test_extract_themes_negative():
    """Test extraction of negative themes."""
    keywords = ["frontal"]
    sentiment_rules = {
        "positive": ["increased"],
        "negative": ["decreased"]
    }
    
    text = "Decreased frontal connectivity."
    themes = extract_themes(text, keywords, sentiment_rules)
    
    assert len(themes) > 0
    assert themes[0]["sentiment"] == "negative"


def test_extract_themes_no_match():
    """Test when no keywords match."""
    keywords = ["nonexistent"]
    sentiment_rules = {}
    
    text = "Some random text."
    themes = extract_themes(text, keywords, sentiment_rules)
    
    assert len(themes) == 0


def test_generate_themes_json():
    """Test aggregation logic."""
    studies = [
        {"qualitative_desc": "Increased auditory connectivity."},
        {"qualitative_desc": "Increased auditory connectivity."},
        {"qualitative_desc": "Decreased frontal connectivity."}
    ]
    
    methodology = {
        "keywords": ["auditory", "frontal"],
        "sentiment_rules": {
            "positive": ["increased"],
            "negative": ["decreased"]
        }
    }
    
    result = generate_themes_json(studies, methodology)
    
    assert "themes" in result
    assert result["themes"]["auditory"]["count"] == 2
    assert result["themes"]["auditory"]["sentiment_breakdown"]["positive"] == 2
    assert result["themes"]["frontal"]["count"] == 1
    assert result["themes"]["frontal"]["sentiment_breakdown"]["negative"] == 1


def test_run_narrative_logic_integration():
    """Test full pipeline execution with temporary files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # 1. Create Config
        config_data = {
            "keywords": ["test"],
            "sentiment_rules": {"positive": ["good"], "negative": ["bad"]}
        }
        config_file = tmp_path / "methodology.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # 2. Create Input CSV
        csv_file = tmp_path / "extracted.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["qualitative_desc"])
            writer.writeheader()
            writer.writerow({"qualitative_desc": "Good test result"})
            writer.writerow({"qualitative_desc": "Bad test result"})
        
        # 3. Run Logic
        output_file = tmp_path / "themes.json"
        result = run_narrative_logic(
            csv_path=csv_file,
            config_path=config_file,
            output_path=output_file
        )
        
        # 4. Verify Output File Exists
        assert output_file.exists()
        
        # 5. Verify Content
        with open(output_file, 'r') as f:
            json_result = json.load(f)
        
        assert json_result["total_studies_processed"] == 2
        assert "test" in json_result["themes"]
        assert json_result["themes"]["test"]["count"] == 2
