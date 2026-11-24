"""
Streaming Chunker
-----------------
Utility generator that yields fixed‑size chunks from a file‑like
object. Used by the OpenNeuro fetcher to stream large archives without
loading them entirely into memory.
"""

from typing import Generator, BinaryIO


def chunked_reader(file_obj: BinaryIO, chunk_size: int = 1024 * 1024) -> Generator[bytes, None, None]:
    """
    Yield ``chunk_size``‑byte chunks from ``file_obj`` until EOF.

    Parameters
    ----------
    file_obj : BinaryIO
        Open file object in binary mode.
    chunk_size : int, optional
        Size of each chunk in bytes (default 1 MiB).

    Yields
    ------
    bytes
        Next chunk of data.
    """
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk
