import unittest
from unittest.mock import patch, MagicMock, mock_open
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import os

# Ensure we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.fetch.pubmed_fetcher import (
    _build_esearch_params,
    _build_efetch_params,
    _parse_esearch_response,
    _parse_efetch_response,
    fetch_pubmed_abstracts
)

class TestPubMedFetcherLogic(unittest.TestCase):

    def test_build_esearch_params(self):
        """Test ESearch parameter construction."""
        params = _build_esearch_params("cancer", 2010, 2020, 500)
        self.assertEqual(params["db"], "pubmed")
        self.assertIn("2010/2010", params["term"])
        self.assertIn("2020/2020", params["term"])
        self.assertEqual(params["retmax"], 500)
        self.assertEqual(params["retmode"], "xml")

    def test_build_efetch_params(self):
        """Test EFetch parameter construction."""
        params = _build_efetch_params(["12345", "67890"])
        self.assertEqual(params["db"], "pubmed")
        self.assertEqual(params["id"], "12345,67890")
        self.assertEqual(params["rettype"], "abstract")

    def test_parse_esearch_response_valid(self):
        """Test parsing a valid ESearch XML response."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <eSearchResult>
            <Count>2</Count>
            <RetMax>2</RetMax>
            <RetStart>0</RetStart>
            <QueryKey>1</QueryKey>
            <WebEnv>NCID_12345</WebEnv>
            <IdList>
                <Id>12345</Id>
                <Id>67890</Id>
            </IdList>
        </eSearchResult>"""
        
        ids = _parse_esearch_response(xml_content)
        self.assertEqual(len(ids), 2)
        self.assertIn("12345", ids)
        self.assertIn("67890", ids)

    def test_parse_esearch_response_empty(self):
        """Test parsing an empty ESearch XML response."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <eSearchResult>
            <Count>0</Count>
            <IdList>
            </IdList>
        </eSearchResult>"""
        
        ids = _parse_esearch_response(xml_content)
        self.assertEqual(len(ids), 0)

    def test_parse_efetch_response_valid(self):
        """Test parsing a valid EFetch XML response."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <PubmedArticles>
            <PubmedArticle>
                <MedlineCitation Status="MEDLINE" Owner="NLM">
                    <PMID Version="1">12345</PMID>
                    <Article>
                        <Journal>
                            <JournalIssue>
                                <PubDate>
                                    <Year>2020</Year>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                        <ArticleTitle>Test Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>This is a test abstract.</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author>
                                <LastName>Doe</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                        </AuthorList>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticles>"""
        
        records = _parse_efetch_response(xml_content)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["pmid"], "12345")
        self.assertEqual(records[0]["title"], "Test Title")
        self.assertEqual(records[0]["abstract"], "This is a test abstract.")
        self.assertEqual(records[0]["year"], "2020")
        self.assertEqual(records[0]["authors"], ["John Doe"])
        self.assertEqual(records[0]["source"], "pubmed")

    def test_parse_efetch_response_multiple_abstracts(self):
        """Test parsing EFetch with multiple abstract text blocks."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <PubmedArticles>
            <PubmedArticle>
                <MedlineCitation Status="MEDLINE" Owner="NLM">
                    <PMID Version="1">12345</PMID>
                    <Article>
                        <Journal>
                            <JournalIssue>
                                <PubDate>
                                    <Year>2020</Year>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                        <ArticleTitle>Test Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>Background part.</AbstractText>
                            <AbstractText>Methods part.</AbstractText>
                        </Abstract>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticles>"""
        
        records = _parse_efetch_response(xml_content)
        self.assertEqual(len(records), 1)
        self.assertIn("Background part.", records[0]["abstract"])
        self.assertIn("Methods part.", records[0]["abstract"])

    @patch('src.data.fetch.pubmed_fetcher._fetch_with_backoff')
    @patch('src.data.fetch.pubmed_fetcher.ET.fromstring')
    def test_fetch_pubmed_abstracts_integration_mock(self, mock_et_fromstring, mock_fetch):
        """Test the fetch function with mocked network calls."""
        # Mock ESearch response
        esearch_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <eSearchResult>
            <Count>2</Count>
            <IdList><Id>111</Id><Id>222</Id></IdList>
        </eSearchResult>"""
        
        # Mock EFetch response
        efetch_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <PubmedArticles>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>111</PMID>
                    <Article>
                        <Journal><JournalIssue><PubDate><Year>2020</Year></PubDate></JournalIssue></Journal>
                        <ArticleTitle>First</ArticleTitle>
                        <Abstract><AbstractText>Text 1</AbstractText></Abstract>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>222</PMID>
                    <Article>
                        <Journal><JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue></Journal>
                        <ArticleTitle>Second</ArticleTitle>
                        <Abstract><AbstractText>Text 2</AbstractText></Abstract>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticles>"""
        
        mock_fetch.side_effect = [esearch_xml, efetch_xml]
        mock_et_fromstring.side_effect = [ET.fromstring(esearch_xml), ET.fromstring(efetch_xml)]
        
        # Mock Path operations
        with patch('pathlib.Path.mkdir'):
            with patch('builtins.open', mock_open()) as mock_file:
                records = fetch_pubmed_abstracts("test", 2020, 2021, max_total=10, output_path=Path("test.jsonl"))
                
                self.assertEqual(len(records), 2)
                self.assertEqual(records[0]["pmid"], "111")
                self.assertEqual(records[1]["pmid"], "222")

    def test_year_filtering_logic(self):
        """Verify that the search term construction includes year filtering."""
        params = _build_esearch_params("diabetes", 2005, 2010, 100)
        term = params["term"]
        self.assertIn("2005/2005", term)
        self.assertIn("2010/2010", term)
        self.assertIn("Date - Publication", term)
