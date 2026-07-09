"""
Mock API response fixtures for OpenAlex, Semantic Scholar, and arXiv.

These fixtures provide realistic, deterministic JSON structures that mimic
the actual API responses from OpenAlex, Semantic Scholar, and arXiv.
They are used for testing search and screening logic without requiring
live API calls.

Each fixture includes:
- Realistic metadata fields (title, year, abstract, DOI, authors)
- Fields relevant to trust/deepfake research
- Proper nesting structures matching the actual APIs
"""

import json
from typing import Dict, List, Any


def get_openalex_response(query: str = "deepfake trust") -> Dict[str, Any]:
    """
    Mock OpenAlex API response.
    
    OpenAlex returns a list of works with fields: id, title, publication_year,
    abstract_inverted_index (or abstract), authors, ids (DOI, etc.)
    """
    return {
        "meta": {
            "count": 2,
            "per_page": 25,
            "page": 1,
            "total_pages": 1
        },
        "results": [
            {
                "id": "https://openalex.org/W3123456789",
                "doi": "https://doi.org/10.1038/s41586-021-03456-7",
                "title": "Trust perception in AI-generated faces: A meta-analytic review",
                "display_name": "Trust perception in AI-generated faces: A meta-analytic review",
                "publication_year": 2023,
                "publication_date": "2023-03-15",
                "source": {
                    "id": "https://openalex.org/S12345",
                    "display_name": "Nature Human Behaviour"
                },
                "abstract_inverted_index": {
                    "trust": [0, 15, 45],
                    "deepfake": [20, 50],
                    "perception": [10, 35],
                    "meta": [60, 80]
                },
                "abstract": "This study examines trust perception in deepfake and AI-generated facial stimuli. "
                            "We conducted a meta-analysis of 45 studies examining trustworthiness ratings. "
                            "Results indicate a significant effect size (d = -0.45) for deepfake faces compared to real faces. "
                            "Moderator analysis reveals that media literacy and realism perception significantly impact trust ratings.",
                "authorships": [
                    {
                        "author": {
                            "id": "https://openalex.org/A111111",
                            "display_name": "Jane Smith"
                        },
                        "raw_author_name": "Jane Smith",
                        "is_corresponding": True
                    },
                    {
                        "author": {
                            "id": "https://openalex.org/A222222",
                            "display_name": "John Doe"
                        },
                        "raw_author_name": "John Doe",
                        "is_corresponding": False
                    }
                ],
                "cited_by_count": 12,
                "is_retracted": False
            },
            {
                "id": "https://openalex.org/W9876543210",
                "doi": "https://doi.org/10.1145/3456789.3456790",
                "title": "AI-Generated Faces and Trust: Experimental Evidence from a Large-Scale Study",
                "display_name": "AI-Generated Faces and Trust: Experimental Evidence from a Large-Scale Study",
                "publication_year": 2022,
                "publication_date": "2022-11-01",
                "source": {
                    "id": "https://openalex.org/S67890",
                    "display_name": "Proceedings of CHI"
                },
                "abstract_inverted_index": {
                    "trust": [5, 25, 55],
                    "ai": [0, 15],
                    "face": [10, 30],
                    "generated": [15, 35]
                },
                "abstract": "We present a large-scale experimental study (N=2,500) on trust perception of AI-generated faces. "
                            "Participants rated trustworthiness of real and deepfake faces. "
                            "We found a medium effect size (d = -0.38) with significant heterogeneity (I² = 65%). "
                            "Moderators included face realism and participant media literacy.",
                "authorships": [
                    {
                        "author": {
                            "id": "https://openalex.org/A333333",
                            "display_name": "Alice Johnson"
                        },
                        "raw_author_name": "Alice Johnson",
                        "is_corresponding": True
                    }
                ],
                "cited_by_count": 8,
                "is_retracted": False
            }
        ]
    }


def get_semantic_scholar_response(query: str = "deepfake trust") -> Dict[str, Any]:
    """
    Mock Semantic Scholar API response.
    
    Semantic Scholar returns a list of papers with fields: title, year, abstract,
    venue, authors, externalIds (DOI), citationCount.
    """
    return {
        "total": 2,
        "limit": 1000,
        "offset": 0,
        "data": [
            {
                "paperId": "a1b2c3d4e5f6",
                "title": "Deepfake Detection and Trust: A Comprehensive Analysis",
                "year": 2023,
                "abstract": "This paper investigates the relationship between deepfake detection capabilities and trust perception. "
                            "Using a sample of 1,200 participants, we measured trust ratings for real and synthetic faces. "
                            "Results show a significant reduction in trust for deepfakes (d = -0.52, p < 0.001). "
                            "We also examined moderator variables including age, gender, and digital literacy.",
                "venue": "IEEE Symposium on Security and Privacy",
                "authors": [
                    {"name": "Robert Chen", "authorId": "auth_001"},
                    {"name": "Maria Garcia", "authorId": "auth_002"}
                ],
                "externalIds": {
                    "DOI": "10.1109/SP46215.2023.123456"
                },
                "citationCount": 15,
                "isOpenAccess": True,
                "openAccessPdf": {
                    "url": "https://example.com/paper1.pdf",
                    "status": "public"
                }
            },
            {
                "paperId": "f6e5d4c3b2a1",
                "title": "The Psychology of AI-Generated Faces: Trust, Uncanny Valley, and Moderating Factors",
                "year": 2021,
                "abstract": "We explore the psychological mechanisms underlying trust in AI-generated faces. "
                            "Three experiments (N=900) examined the role of the uncanny valley and media literacy. "
                            "Meta-analytic aggregation yielded an overall effect size of d = -0.41. "
                            "Moderator analysis indicated that media literacy significantly attenuates the trust deficit.",
                "venue": "Journal of Experimental Psychology: General",
                "authors": [
                    {"name": "Sarah Williams", "authorId": "auth_003"},
                    {"name": "David Lee", "authorId": "auth_004"},
                    {"name": "Emily Brown", "authorId": "auth_005"}
                ],
                "externalIds": {
                    "DOI": "10.1037/xge0001234"
                },
                "citationCount": 24,
                "isOpenAccess": False,
                "openAccessPdf": None
            }
        ]
    }


def get_arxiv_response(query: str = "deepfake trust") -> Dict[str, Any]:
    """
    Mock arXiv API response.
    
    arXiv returns a feed with entries containing: title, published, summary,
    authors, doi (if available), arxiv_id.
    """
    return {
        "feed": {
            "title": "arXiv Query Results",
            "updated": "2024-01-15T10:30:00Z",
            "total_results": 2,
            "entries": [
                {
                    "id": "http://arxiv.org/abs/2301.12345",
                    "updated": "2023-01-20T00:00:00Z",
                    "published": "2023-01-15T00:00:00Z",
                    "title": "Trust Metrics in Deepfake Detection: A Systematic Review",
                    "summary": "We present a systematic review of trust metrics used in deepfake detection literature. "
                               "Analyzing 67 studies, we find that trust perception is consistently lower for deepfakes. "
                               "Effect sizes range from d = -0.30 to d = -0.60. "
                               "We identify key moderators including face realism, context, and viewer expertise. "
                               "Implications for policy and detection system design are discussed.",
                    "author": [
                        {
                            "name": "Michael Zhang",
                            "arxiv_id": "1234567"
                        },
                        {
                            "name": "Lisa Wang",
                            "arxiv_id": "7654321"
                        }
                    ],
                    "link": [
                        {"href": "http://arxiv.org/abs/2301.12345", "rel": "alternate", "type": "text/html"},
                        {"href": "http://arxiv.org/pdf/2301.12345", "rel": "related", "type": "application/pdf"}
                    ],
                    "arxiv_primary_category": {
                        "term": "cs.CV"
                    },
                    "category": [
                        {"term": "cs.CV"},
                        {"term": "cs.CR"},
                        {"term": "psych.GN"}
                    ]
                },
                {
                    "id": "http://arxiv.org/abs/2209.67890",
                    "updated": "2022-09-25T00:00:00Z",
                    "published": "2022-09-20T00:00:00Z",
                    "title": "AI-Generated Faces and Trustworthiness: Experimental Evidence from Pre-registered Studies",
                    "summary": "We report results from three pre-registered experiments (N=1,800) examining trust in AI-generated faces. "
                               "Using GAN-synthesized and diffusion-generated faces, we found consistent trust deficits. "
                               "Pooled effect size: d = -0.47, 95% CI [-0.58, -0.36]. "
                               "Moderator analysis shows that realism ratings and media literacy significantly predict trust. "
                               "We also report heterogeneity statistics (I² = 58%, Q = 45.2, p < 0.001).",
                    "author": [
                        {
                            "name": "Thomas Anderson",
                            "arxiv_id": "9988776"
                        }
                    ],
                    "link": [
                        {"href": "http://arxiv.org/abs/2209.67890", "rel": "alternate", "type": "text/html"},
                        {"href": "http://arxiv.org/pdf/2209.67890", "rel": "related", "type": "application/pdf"}
                    ],
                    "arxiv_primary_category": {
                        "term": "cs.CV"
                    },
                    "category": [
                        {"term": "cs.CV"},
                        {"term": "stat.AP"}
                    ]
                }
            ]
        }
    }


def get_all_fixtures() -> Dict[str, Dict[str, Any]]:
    """
    Return all mock API response fixtures in a single dictionary.
    
    Returns:
        Dict mapping source name to its mock response data.
    """
    return {
        "openalex": get_openalex_response(),
        "semantic_scholar": get_semantic_scholar_response(),
        "arxiv": get_arxiv_response()
    }