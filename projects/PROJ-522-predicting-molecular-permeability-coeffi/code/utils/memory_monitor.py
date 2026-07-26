import os
import sys

def get_memory_usage_mb():
    """
    Get current memory usage in MB.
    """
    if sys.platform == 'win32':
        # Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong
        c_size_t = ctypes.c_size_t
        c_long = ctypes.c_long
        
        PROCESS_MEMORY_COUNTERS = 8
        pmc = PROCESS_MEMORY_COUNTERS
        h_process = ctypes.windll.kernel32.OpenProcess(0x10 | 0x400, False, os.getpid())
        if h_process:
            info = c_ulong * 3
            if kernel32.GetProcessMemoryInfo(h_process, ctypes.cast(info, ctypes.POINTER(ctypes.c_ulong)), ctypes.sizeof(info)):
                # Working set size
                return info[1] / (1024 * 1024)
            else:
                return 0
        else:
            return 0
    else:
        # Unix-like
        try:
            with open(f'/proc/{os.getpid()}/statm', 'r') as f:
                rss_pages = int(f.read().split()[1])
                page_size = os.sysconf('SC_PAGE_SIZE')
                return (rss_pages * page_size) / (1024 * 1024)
        except Exception:
            return 0

def check_memory_limit(limit_mb: int = 2048):
    """
    Check if current memory usage exceeds the limit.
    Raises MemoryError if limit exceeded.
    """
    usage = get_memory_usage_mb()
    if usage > limit_mb:
        raise MemoryError(f"Memory usage {usage:.2f} MB exceeds limit {limit_mb} MB")
    return usage
