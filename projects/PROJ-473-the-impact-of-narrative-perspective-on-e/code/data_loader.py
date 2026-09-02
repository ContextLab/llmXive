import os
import re
import json
import hashlib
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from gutenberg import Gutenberg

def fetch_gutenberg_corpus(output_dir: str, authors: Optional[List[str]] = None) -> int:
    """
    Fetch stories from Project Gutenberg using the gutenberg library.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    gutenberg = Gutenberg()
    story_count = 0

    for author in authors:
        try:
            books = gutenberg.get_books_by_author(author)
            for book_id in books:
                try:
                    book = gutenberg.get_book(book_id)
                    text = book.content
                    # Extract stories based on length (minimum 50 words)
                    stories = re.split(r'\n\s*\n', text)  # Split by empty lines
                    for story in stories:
                        if len(story.split()) > 50:
                            story_filename = os.path.join(output_dir, f"story_{hashlib.md5(story.encode('utf-8')).hexdigest()}.txt")
                            with open(story_filename, "w", encoding="utf-8") as f:
                                f.write(story)
                            story_count += 1
                except Exception as e:
                    print(f"Error fetching book {book_id} by {author}: {e}")
        except Exception as e:
            print(f"Error getting books by {author}: {e}")

    if story_count < 50:
        print(f"ERROR: Corpus size < 50. Cannot proceed with SC-001 validation.")
        raise ValueError("Corpus size less than 50")

    return story_count