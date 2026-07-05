#pragma once
#include <atomic>
#include <cstddef>
#include <new>

// Padded counter struct: aligned to cache line boundaries to prevent false sharing
// Target size: >= 192 bytes (3 cache lines of 64 bytes) to ensure isolation even with overhead
// Or simply align the struct to 64 bytes and ensure size is large enough.
// The task says "padded (>=192 bytes)".

struct alignas(64) PaddedCounter {
    std::atomic<long> value;
    // Pad to ensure total size is at least 192 bytes (3 cache lines)
    // atomic<long> is 8 bytes.
    // We need 184 bytes of padding.
    char padding[184]; 
};

// Verify size at compile time if possible, or runtime check in verify_layout
static_assert(sizeof(PaddedCounter) >= 192, "PaddedCounter must be at least 192 bytes");
static_assert(alignof(PaddedCounter) == 64, "PaddedCounter must be aligned to 64 bytes");
