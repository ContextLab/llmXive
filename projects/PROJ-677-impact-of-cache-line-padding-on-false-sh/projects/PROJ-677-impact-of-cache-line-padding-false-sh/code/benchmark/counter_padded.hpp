#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstdint>
#include <atomic>
#include <cstddef>

// Padded structure: Each field is aligned to a cache line (64 bytes).
// This ensures that each atomic variable resides on its own cache line,
// preventing false sharing.
// Size: 3 * 64 = 192 bytes.

// Helper macro for cache line size
#ifndef CACHE_LINE_SIZE
#define CACHE_LINE_SIZE 64
#endif

struct PaddedCounter {
    alignas(CACHE_LINE_SIZE) std::atomic<long> a;
    alignas(CACHE_LINE_SIZE) std::atomic<long> b;
    alignas(CACHE_LINE_SIZE) std::atomic<long> c;
};

static_assert(sizeof(PaddedCounter) >= 192, "PaddedCounter must be at least 192 bytes");

#endif // COUNTER_PADDED_HPP