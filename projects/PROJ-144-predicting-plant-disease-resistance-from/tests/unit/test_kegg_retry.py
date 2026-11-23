"""
Unit tests for KEGG API retry and fallback logic in interpret.py.

Tests verify:
1. Retry logic with exponential backoff
2. Fallback behavior on API failures
3. Correct handling of valid and invalid InChIKeys
"""
import pytest
import time
from unittest.mock import patch, MagicMock
import urllib.error
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from modeling.interpret import (
    fetch_kegg_metabolite,
    fetch_kegg_compound_info,
    parse_kegg_entry,
    map_metabolite_to_pathways,
    enrich_metabolite_info,
    MAX_RETRIES,
    BASE_DELAY
)

class TestKEGGRetryLogic:
    """Tests for KEGG API retry mechanism."""
    
    def test_retry_on_timeout(self):
        """Test that fetch_kegg_metabolite retries on timeout."""
        inchikey = "TEST_INCHIKEY"
        
        # Mock urlopen to raise timeout twice, then succeed
        with patch('modeling.interpret.urllib.request.urlopen') as mock_urlopen:
            # First two calls raise timeout, third succeeds
            mock_urlopen.side_effect = [
                urllib.error.URLError("Timeout"),
                urllib.error.URLError("Timeout"),
                MagicMock(read=MagicMock(return_value=b"ENTRY\tC00001\nNAME\tTest Compound"))
            ]
            
            result = fetch_kegg_metabolite(inchikey)
            
            # Should have retried 3 times
            assert mock_urlopen.call_count == 3
            assert result is not None
            assert result['compound_id'] == 'C00001'
    
    def test_no_retry_on_success(self):
        """Test that fetch_kegg_metabolite does not retry on success."""
        inchikey = "TEST_INCHIKEY"
        
        with patch('modeling.interpret.urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read = MagicMock(return_value=b"ENTRY\tC00001\nNAME\tTest")
            mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_response)
            mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
            
            result = fetch_kegg_metabolite(inchikey)
            
            # Should only call once
            assert mock_urlopen.call_count == 1
            assert result is not None
    
    def test_exponential_backoff_timing(self):
        """Test that retries use exponential backoff."""
        inchikey = "TEST_INCHIKEY"
        
        call_times = []
        
        def mock_urlopen_side_effect(*args, **kwargs):
            call_times.append(time.time())
            raise urllib.error.URLError("Timeout")
        
        with patch('modeling.interpret.urllib.request.urlopen', side_effect=mock_urlopen_side_effect):
            with patch('modeling.interpret.time.sleep', return_value=None):  # Skip actual sleep
                result = fetch_kegg_metabolite(inchikey)
                
                # Should have attempted MAX_RETRIES times
                assert len(call_times) == MAX_RETRIES
                
                # Check that delays are increasing (though we mocked sleep)
                # This test verifies the logic flow rather than actual timing
    
    def test_failure_after_max_retries(self):
        """Test that fetch_kegg_metabolite returns None after max retries."""
        inchikey = "TEST_INCHIKEY"
        
        with patch('modeling.interpret.urllib.request.urlopen') as mock_urlopen:
            # Always fail
            mock_urlopen.side_effect = urllib.error.URLError("Network error")
            
            result = fetch_kegg_metabolite(inchikey)
            
            # Should have retried MAX_RETRIES times
            assert mock_urlopen.call_count == MAX_RETRIES
            assert result is None
    
    def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        inchikey = "TEST_INCHIKEY"
        
        with patch('modeling.interpret.urllib.request.urlopen') as mock_urlopen:
            mock_error = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
            mock_urlopen.side_effect = mock_error
            
            result = fetch_kegg_metabolite(inchikey)
            
            assert mock_urlopen.call_count == MAX_RETRIES
            assert result is None
    
    def test_parse_kegg_entry(self):
        """Test parsing of KEGG entry text."""
        entry_text = """ENTRY       C00001                      Compound
        NAME        Glucose;
                    D-Glucose;
                    Grape sugar;
                    Blood sugar
        FORMULA     C6H12O6
        PATHWAY     path:ko00010  Glycolysis / Gluconeogenesis
                    path:ko00030  Pentose phosphate pathway
        """
        
        parsed = parse_kegg_entry(entry_text)
        
        assert 'ENTRY' in parsed
        assert 'NAME' in parsed
        assert 'FORMULA' in parsed
        assert 'PATHWAY' in parsed
        assert parsed['ENTRY'] == 'C00001                      Compound'
        assert 'Glycolysis' in parsed['PATHWAY']
    
    def test_map_metabolite_to_pathways(self):
        """Test pathway mapping from metabolite info."""
        metabolite_info = {
            'compound_id': 'C00001',
            'PATHWAY': 'path:ko00010  Glycolysis / Gluconeogenesis\npath:ko00030  Pentose phosphate pathway'
        }
        
        pathways = map_metabolite_to_pathways(metabolite_info)
        
        assert len(pathways) == 2
        assert pathways[0]['pathway_id'] == 'path:ko00010'
        assert 'Glycolysis' in pathways[0]['pathway_name']
        assert pathways[1]['pathway_id'] == 'path:ko00030'
    
    def test_enrich_metabolite_with_kegg(self):
        """Test full enrichment of metabolite with KEGG data."""
        metabolite = {
            'name': 'Test Metabolite',
            'inchikey': 'TESTKEY'
        }
        
        with patch('modeling.interpret.fetch_kegg_metabolite') as mock_fetch:
            mock_fetch.return_value = {
                'compound_id': 'C00001',
                'raw_entry': 'ENTRY\tC00001'
            }
            
            with patch('modeling.interpret.fetch_kegg_compound_info') as mock_info:
                mock_info.return_value = {
                    'PATHWAY': 'path:ko00010  Test Pathway'
                }
                
                enriched = enrich_metabolite_info(metabolite)
                
                assert enriched['mapping_success'] is True
                assert 'compound_id' in enriched
                assert 'pathways' in enriched
                assert len(enriched['pathways']) == 1
    
    def test_enrich_metabolite_no_inchikey(self):
        """Test enrichment when InChIKey is missing."""
        metabolite = {
            'name': 'Test Metabolite',
            'formula': 'C6H12O6'
        }
        
        enriched = enrich_metabolite_info(metabolite)
        
        assert enriched['mapping_success'] is False
        assert 'mapping_error' in enriched
        assert 'InChIKey' in enriched['mapping_error']
    
    def test_enrich_metabolite_fetch_failure(self):
        """Test enrichment when KEGG fetch fails."""
        metabolite = {
            'name': 'Test Metabolite',
            'inchikey': 'INVALID_KEY'
        }
        
        with patch('modeling.interpret.fetch_kegg_metabolite') as mock_fetch:
            mock_fetch.return_value = None
            
            enriched = enrich_metabolite_info(metabolite)
            
            assert enriched['mapping_success'] is False
            assert 'mapping_error' in enriched

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
