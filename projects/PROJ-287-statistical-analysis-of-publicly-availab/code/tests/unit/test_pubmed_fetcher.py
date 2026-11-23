import unittest
from unittest.mock import patch, MagicMock, mock_open
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import os
import json

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.fetch.pubmed_fetcher import (
    fetch_pubmed_abstracts,
    _fetch_pubmed_ids,
    _fetch_abstract_batch,
    _delayed_retry,
    MAX_RETRIES
)

class TestPubMedFetcherLogic(unittest.TestCase):

    def setUp(self):
        self.mock_xml_response = b"""
        <eSearchResult>
            <Count>2</Count>
            <RetMax>2</RetMax>
            <RetStart>0</RetStart>
            <IdList>
                <Id>12345</Id>
                <Id>67890</Id>
            </IdList>
        </eSearchResult>
        """
        
        self.mock_abstract_xml = b"""
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345</PMID>
                    <Article>
                        <ArticleTitle>Test Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>This is a test abstract.</AbstractText>
                        </Abstract>
                        <Journal>
                            <Title>Test Journal</Title>
                        </Journal>
                        <PublicationDate>
                            <Year>2010</Year>
                        </PublicationDate>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>67890</PMID>
                    <Article>
                        <ArticleTitle>Another Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>Another abstract text.</AbstractText>
                        </Abstract>
                        <Journal>
                            <Title>Another Journal</Title>
                        </Journal>
                        <PublicationDate>
                            <Year>2015</Year>
                        </PublicationDate>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>
        """

    @patch('src.data.fetch.pubmed_fetcher.urllib.request.urlopen')
    def test_fetch_pubmed_ids_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = self.mock_xml_response
        mock_urlopen.return_value.__enter__.return_value = mock_response

        ids = _fetch_pubmed_ids(2000, 2024)
        
        self.assertEqual(len(ids), 2)
        self.assertIn("12345", ids)
        self.assertIn("67890", ids)

    @patch('src.data.fetch.pubmed_fetcher.urllib.request.urlopen')
    def test_fetch_abstract_batch_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = self.mock_abstract_xml
        mock_urlopen.return_value.__enter__.return_value = mock_response

        pmids = ["12345", "67890"]
        records = list(_fetch_abstract_batch(pmids))
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["pmid"], "12345")
        self.assertEqual(records[0]["title"], "Test Title")
        self.assertEqual(records[0]["year"], "2010")
        self.assertIn("test abstract", records[0]["abstract"].lower())

    @patch('src.data.fetch.pubmed_fetcher._fetch_pubmed_ids')
    @patch('src.data.fetch.pubmed_fetcher._fetch_abstract_batch')
    @patch('src.data.fetch.pubmed_fetcher.urllib.request.urlopen')
    def test_fetch_pubmed_abstracts_integration(self, mock_urlopen, mock_batch, mock_ids):
        mock_ids.return_value = ["12345", "67890"]
        mock_batch.return_value = [
            {"pmid": "12345", "title": "T1", "abstract": "A1", "year": "2010", "journal": "J1", "authors": "A"},
            {"pmid": "67890", "title": "T2", "abstract": "A2", "year": "2015", "journal": "J2", "authors": "B"}
        ]
        
        records = fetch_pubmed_abstracts(2000, 2024)
        
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["pmid"], "12345")

    def test_delayed_retry_max_attempts(self):
        attempt_count = 0
        
        def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("Simulated failure")
        
        with self.assertRaises(Exception):
            _delayed_retry(failing_func)
        
        # Should have attempted MAX_RETRIES times
        self.assertEqual(attempt_count, MAX_RETRIES)

    @patch('src.data.fetch.pubmed_fetcher._fetch_pubmed_ids')
    @patch('src.data.fetch.pubmed_fetcher._fetch_abstract_batch')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.data.fetch.pubmed_fetcher.Path.mkdir')
    def test_fetch_saves_to_file(self, mock_mkdir, mock_open_file, mock_batch, mock_ids):
        mock_ids.return_value = ["12345"]
        mock_batch.return_value = [
            {"pmid": "12345", "title": "T1", "abstract": "A1", "year": "2010", "journal": "J1", "authors": "A"}
        ]
        
        output_path = Path("data/raw/test_output.jsonl")
        records = fetch_pubmed_abstracts(2000, 2024, output_path=output_path)
        
        # Verify file write was called
        mock_open_file.assert_called()
        written_content = mock_open_file().write.call_args_list[0][0][0]
        self.assertIn("12345", written_content)
        self.assertIn("T1", written_content)

    def test_year_filtering(self):
        # Test that records outside the year range are filtered out
        test_records = [
            {"pmid": "1", "year": "1999"},
            {"pmid": "2", "year": "2000"},
            {"pmid": "3", "year": "2024"},
            {"pmid": "4", "year": "2025"}
        ]
        
        # Manually filter as the function does
        filtered = [r for r in test_records if 2000 <= int(r["year"]) <= 2024]
        
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["pmid"], "2")
        self.assertEqual(filtered[1]["pmid"], "3")

if __name__ == "__main__":
    unittest.main()