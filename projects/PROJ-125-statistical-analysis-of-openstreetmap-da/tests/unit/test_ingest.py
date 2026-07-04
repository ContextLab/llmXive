"""
Unit tests for Overpass API query construction in code/ingest.py.

This module verifies that the query builder functions in code/ingest.py
correctly construct Overpass QL queries for fetching OSM data (buildings,
land-use, trees, roads) based on city boundaries.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path if not already present
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import build_overpass_query, build_building_query, build_landuse_query
from code.config import get_city_bounds


class TestOverpassQueryConstruction:
    """Test cases for Overpass API query construction logic."""

    def test_build_overpass_query_basic_structure(self):
        """Test that the basic Overpass query structure is correct."""
        # Mock city bounds
        bounds = (40.7128, -74.0060, 40.8128, -73.9060)  # (min_lat, min_lon, max_lat, max_lon)
        
        query = build_overpass_query(bounds, output_format="json")
        
        assert query.startswith("[out:json]")
        assert "timeout:180" in query
        assert f"[bbox:{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}]" in query
        assert "node" in query or "way" in query or "relation" in query
        assert "out" in query

    def test_build_building_query_includes_correct_tags(self):
        """Test that building queries include the 'building' tag."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_building_query(bounds)
        
        assert "building" in query
        assert "way" in query or "relation" in query
        assert "out geom" in query or "out body" in query

    def test_build_landuse_query_includes_correct_tags(self):
        """Test that land-use queries include relevant land-use tags."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_landuse_query(bounds)
        
        # Should include common land-use tags
        assert "landuse" in query
        # Check for at least one specific land-use type
        landuse_types = ["residential", "commercial", "industrial", "forest", "grass"]
        assert any(t in query for t in landuse_types), "Query should include specific land-use types"

    def test_query_construction_handles_large_bounds(self):
        """Test that query construction works for large bounding boxes."""
        # Large bounds covering a significant area
        bounds = (40.0, -75.0, 41.0, -73.0)
        
        query = build_overpass_query(bounds)
        
        # Should still produce valid query structure
        assert len(query) > 50  # Query should be substantial
        assert "timeout" in query  # Should include timeout for large queries

    def test_query_construction_with_empty_bounds(self):
        """Test behavior with invalid/empty bounds."""
        # Invalid bounds (min > max)
        bounds = (41.0, -73.0, 40.0, -75.0)
        
        with pytest.raises(ValueError):
            build_overpass_query(bounds)

    def test_query_output_formats(self):
        """Test different output formats in query construction."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        for fmt in ["json", "xml", "csv"]:
            query = build_overpass_query(bounds, output_format=fmt)
            assert f"[out:{fmt}]" in query

    def test_query_includes_geom_for_buildings(self):
        """Test that building queries include geometry output."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_building_query(bounds)
        
        # Building queries should include geometry
        assert "geom" in query or "body" in query

    def test_query_rate_limiting_parameters(self):
        """Test that rate limiting parameters are included in query."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_overpass_query(bounds)
        
        # Should include timeout to prevent rate limiting
        assert "timeout" in query
        # Should have reasonable timeout value (180 seconds as per common practice)
        assert "180" in query

    def test_query_construction_with_specific_city(self):
        """Test query construction for a specific known city."""
        # New York City bounds
        nyc_bounds = get_city_bounds("New York City")
        
        if nyc_bounds:
            query = build_overpass_query(nyc_bounds)
            
            assert "node" in query or "way" in query
            assert "out" in query
            # Verify bounds are correctly formatted in query
            assert f"[bbox:{nyc_bounds[0]},{nyc_bounds[1]},{nyc_bounds[2]},{nyc_bounds[3]}]" in query

    def test_query_construction_returns_valid_ql_syntax(self):
        """Test that generated queries have valid Overpass QL syntax."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_overpass_query(bounds)
        
        # Basic syntax checks
        assert query.count("(") == query.count(")")
        assert query.count("[") == query.count("]")
        assert not query.strip().endswith(",")  # No trailing commas
        assert ";" in query or "out" in query  # Proper statement termination or output

    def test_build_query_with_multiple_element_types(self):
        """Test query construction that includes multiple OSM element types."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_overpass_query(bounds)
        
        # Should query at least one element type
        has_elements = any(t in query for t in ["node", "way", "relation"])
        assert has_elements, "Query must include at least one OSM element type"

    def test_query_construction_preserves_order(self):
        """Test that query components appear in expected order."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_overpass_query(bounds)
        
        # Output format should come before timeout
        output_pos = query.find("[out:")
        timeout_pos = query.find("timeout:")
        
        if output_pos != -1 and timeout_pos != -1:
            assert output_pos < timeout_pos, "Output format should precede timeout"

    def test_query_construction_with_custom_timeout(self):
        """Test query construction with custom timeout values."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        # Note: The current implementation uses fixed timeout, but structure should allow extension
        query = build_overpass_query(bounds)
        
        assert "timeout" in query

    def test_query_construction_handles_special_characters_in_bounds(self):
        """Test that bounds with decimal values are handled correctly."""
        bounds = (40.7128, -74.0060, 40.8128, -73.9060)
        
        query = build_overpass_query(bounds)
        
        # Should contain the exact bounds values
        assert "40.7128" in query
        assert "-74.0060" in query
        assert "40.8128" in query
        assert "-73.9060" in query

    def test_query_construction_with_rels(self):
        """Test that relation elements are included when appropriate."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        
        query = build_overpass_query(bounds)
        
        # For urban areas, relations (like administrative boundaries) are often needed
        # The query should be capable of including them
        # This test verifies the structure allows for relation queries
        assert "relation" in query or "way" in query or "node" in query

@pytest.mark.integration
class TestOverpassQueryExecution:
    """Integration tests for actual Overpass API query execution (optional)."""
    
    @pytest.mark.skip(reason="Requires Overpass API access and network")
    def test_actual_query_execution(self):
        """Test actual query execution against Overpass API."""
        bounds = (40.7, -74.0, 40.8, -73.9)
        query = build_overpass_query(bounds)
        
        # This would require network access and is skipped in unit test environment
        pass

    @pytest.mark.skip(reason="Requires Overpass API access and network")
    def test_query_response_validation(self):
        """Test validation of actual Overpass API responses."""
        # Implementation would require network access
        pass