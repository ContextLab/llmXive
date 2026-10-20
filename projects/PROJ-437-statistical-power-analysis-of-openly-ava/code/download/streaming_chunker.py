"""
Streaming Chunker
-----------------
Utility that yields a file‑like object in fixed‑size chunks.
It is used by ``openneuro_fetcher`` when streaming large archives.
"""

from typing import Generator, IO

def chunked_reader(file_obj: IO[bytes], chunk_size: int = 1024 * 1024) -> Generator[bytes, None, None]:
    """
    Yield ``chunk_size``‑byte chunks from ``file_obj`` until EOF.
    """
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        yield data
