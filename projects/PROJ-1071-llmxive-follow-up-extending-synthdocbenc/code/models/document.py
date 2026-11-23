"""
Data models for synthetic document generation and metadata.
Matches the schema defined in contracts/document_schema.yaml
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class MiddleThirdMetadata(BaseModel):
    """
    Metadata describing the 'middle-third' region of a document.
    Used to verify the bias hypothesis (SC-001).
    """
    def __init__(
        self,
        start_page: int,
        end_page: int,
        total_pages: int,
        text_density: float,
        is_valid: bool
    ):
        self.start_page = start_page
        self.end_page = end_page
        self.total_pages = total_pages
        self.text_density = text_density
        self.is_valid = is_valid

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MiddleThirdMetadata':
        cls.validate_required_fields(data, ['start_page', 'end_page', 'total_pages', 'text_density', 'is_valid'], 'MiddleThirdMetadata')
        return super().from_dict(data)

class Page(BaseModel):
    """
    Represents a single page within a document.
    """
    def __init__(
        self,
        page_number: int,
        image_path: Optional[str] = None,
        text_content: Optional[str] = None,
        text_density: Optional[float] = None,
        is_middle_third: bool = False
    ):
        self.page_number = page_number
        self.image_path = image_path
        self.text_content = text_content
        self.text_density = text_density
        self.is_middle_third = is_middle_third

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        return super().from_dict(data)

class Document(BaseModel):
    """
    Represents a complete synthetic document with its metadata.
    Matches the schema in contracts/document_schema.yaml.
    """
    def __init__(
        self,
        document_id: str,
        title: str,
        total_pages: int,
        pdf_path: str,
        middle_third_metadata: MiddleThirdMetadata,
        pages: List[Page],
        checksum: Optional[str] = None
    ):
        self.document_id = document_id
        self.title = title
        self.total_pages = total_pages
        self.pdf_path = pdf_path
        self.middle_third_metadata = middle_third_metadata
        self.pages = pages
        self.checksum = checksum

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Ensure nested objects are serialized correctly
        data['middle_third_metadata'] = self.middle_third_metadata.to_dict()
        data['pages'] = [p.to_dict() for p in self.pages]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        cls.validate_required_fields(
            data,
            ['document_id', 'title', 'total_pages', 'pdf_path', 'middle_third_metadata', 'pages'],
            'Document'
        )
        
        # Reconstruct nested objects
        data['middle_third_metadata'] = MiddleThirdMetadata.from_dict(data['middle_third_metadata'])
        data['pages'] = [Page.from_dict(p) for p in data['pages']]
        
        return super().from_dict(data)
