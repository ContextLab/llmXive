"""
Document and Page models matching contracts/document_schema.yaml.
"""
from typing import Any, Dict, List, Optional
from .base import BaseModel

class MiddleThirdMetadata(BaseModel):
    """Metadata for the middle-third region of a document."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "start_page": {
                    "type": "integer",
                    "required": True,
                    "description": "Starting page index of the middle third"
                },
                "end_page": {
                    "type": "integer",
                    "required": True,
                    "description": "Ending page index of the middle third"
                },
                "text_density": {
                    "type": "number",
                    "required": True,
                    "description": "Text density in the middle third (0.0-1.0)"
                },
                "character_count": {
                    "type": "integer",
                    "required": True,
                    "description": "Total character count in the middle third"
                }
            }
        }

    def __init__(
        self,
        start_page: int,
        end_page: int,
        text_density: float,
        character_count: int
    ):
        data = {
            "start_page": start_page,
            "end_page": end_page,
            "text_density": text_density,
            "character_count": character_count
        }
        self._data = self.validate(data)
        self.start_page = start_page
        self.end_page = end_page
        self.text_density = text_density
        self.character_count = character_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_page": self.start_page,
            "end_page": self.end_page,
            "text_density": self.text_density,
            "character_count": self.character_count
        }

class Page(BaseModel):
    """Page model matching contracts/page_schema.yaml."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique page identifier"
                },
                "page_number": {
                    "type": "integer",
                    "required": True,
                    "description": "Page number (1-indexed)"
                },
                "text_density": {
                    "type": "number",
                    "required": True,
                    "description": "Text density on this page (0.0-1.0)"
                },
                "character_count": {
                    "type": "integer",
                    "required": True,
                    "description": "Character count on this page"
                },
                "layout_info": {
                    "type": "object",
                    "required": False,
                    "description": "Layout information (optional)"
                }
            }
        }

    def __init__(
        self,
        page_id: str,
        page_number: int,
        text_density: float,
        character_count: int,
        layout_info: Optional[Dict[str, Any]] = None
    ):
        data = {
            "page_id": page_id,
            "page_number": page_number,
            "text_density": text_density,
            "character_count": character_count
        }
        if layout_info is not None:
            data["layout_info"] = layout_info
        self._data = self.validate(data)
        self.page_id = page_id
        self.page_number = page_number
        self.text_density = text_density
        self.character_count = character_count
        self.layout_info = layout_info

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "page_id": self.page_id,
            "page_number": self.page_number,
            "text_density": self.text_density,
            "character_count": self.character_count
        }
        if self.layout_info is not None:
            result["layout_info"] = self.layout_info
        return result

class Document(BaseModel):
    """Document model matching contracts/document_schema.yaml."""

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique document identifier"
                },
                "title": {
                    "type": "string",
                    "required": True,
                    "description": "Document title"
                },
                "total_pages": {
                    "type": "integer",
                    "required": True,
                    "description": "Total number of pages"
                },
                "pdf_path": {
                    "type": "string",
                    "required": True,
                    "description": "Path to the PDF file"
                },
                "middle_third": {
                    "type": "object",
                    "required": True,
                    "description": "Middle-third metadata"
                },
                "pages": {
                    "type": "array",
                    "required": True,
                    "description": "List of page metadata"
                }
            }
        }

    def __init__(
        self,
        doc_id: str,
        title: str,
        total_pages: int,
        pdf_path: str,
        middle_third: MiddleThirdMetadata,
        pages: List[Page]
    ):
        data = {
            "doc_id": doc_id,
            "title": title,
            "total_pages": total_pages,
            "pdf_path": pdf_path,
            "middle_third": middle_third.to_dict(),
            "pages": [p.to_dict() for p in pages]
        }
        self._data = self.validate(data)
        self.doc_id = doc_id
        self.title = title
        self.total_pages = total_pages
        self.pdf_path = pdf_path
        self.middle_third = middle_third
        self.pages = pages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "total_pages": self.total_pages,
            "pdf_path": self.pdf_path,
            "middle_third": self.middle_third.to_dict(),
            "pages": [p.to_dict() for p in self.pages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        validated = cls.validate(data)
        middle_third = MiddleThirdMetadata.from_dict(validated['middle_third'])
        pages = [Page.from_dict(p) for p in validated['pages']]
        return cls(
            doc_id=validated['doc_id'],
            title=validated['title'],
            total_pages=validated['total_pages'],
            pdf_path=validated['pdf_path'],
            middle_third=middle_third,
            pages=pages
        )
