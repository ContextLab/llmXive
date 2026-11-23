"""
Unit tests for T040b: Literature-based GPU Conversion Factor generation.
"""

import json
import os
from pathlib import Path
import pytest

# Import the generation logic
from code.analysis.generate_gpu_factor import generate_gpu_factor_documentation, OUTPUT_PATH

class TestLiteratureGpuFactor:
    """Tests for the literature-based GPU factor generation."""

    def test_factor_structure(self):
        """Verify the generated data has required fields."""
        data = generate_gpu_factor_documentation()
        
        assert "conversion_factor" in data
        assert isinstance(data["conversion_factor"], (int, float))
        assert data["conversion_factor"] > 0
        
        assert "limitation" in data
        assert "ESTIMATE" in data["limitation"] or "estimated" in data["limitation"].lower()
        
        assert "citation" in data
        citation = data["citation"]
        assert "title" in citation
        assert "url" in citation or "doi" in citation

    def test_file_generation(self):
        """Verify the script can generate the output file."""
        # Run the main logic
        from code.analysis.generate_gpu_factor import main
        
        # Ensure file is created
        main()
        
        assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} was not created"
        
        # Verify file content
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["conversion_factor"] > 0
        assert data["metadata"]["is_estimated"] is True
        assert "literature" in data["metadata"]["source_type"]

    def test_citation_validity(self):
        """Verify the citation contains required fields."""
        data = generate_gpu_factor_documentation()
        citation = data["citation"]
        
        # At minimum, must have a title and a link (URL or DOI)
        assert len(citation["title"]) > 0
        assert "url" in citation or "doi" in citation

    def test_estimation_flag(self):
        """Verify the JSON explicitly states the metric is estimated."""
        data = generate_gpu_factor_documentation()
        
        # Check the limitation field explicitly mentions estimation
        limitation_text = data.get("limitation", "").lower()
        assert "estimate" in limitation_text or "estimated" in limitation_text
        
        # Check metadata flag
        assert data["metadata"]["is_estimated"] is True
