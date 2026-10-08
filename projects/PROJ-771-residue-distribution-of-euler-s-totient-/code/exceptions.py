class FatalSieveError(Exception):
    """Raised when the sieve fails at a specific integer n."""
    def __init__(self, n: int, error_message: str):
        self.n = n
        self.error_message = error_message
        super().__init__(f"Fatal sieve error at n={n}: {error_message}")

class ResearchIncompleteError(Exception):
    """Raised when required research constants are missing or invalid."""
    def __init__(self, missing_constant: str, message: str):
        self.missing_constant = missing_constant
        self.message = message
        super().__init__(f"Research incomplete: Missing constant '{missing_constant}'. {message}")

class BenchmarkFailure(Exception):
    """Raised when a benchmark target is not met."""
    def __init__(self, elapsed_time: float, limit: float):
        self.elapsed_time = elapsed_time
        self.limit = limit
        super().__init__(f"Benchmark failure: {elapsed_time:.2f}s exceeded limit of {limit:.2f}s")
