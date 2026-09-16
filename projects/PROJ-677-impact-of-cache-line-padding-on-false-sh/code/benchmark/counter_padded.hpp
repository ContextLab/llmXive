#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstdint>
#include <atomic>
#include <new>

// Cache line size constant (typically 64 bytes on modern x86_64)
constexpr size_t CACHE_LINE_SIZE = 64;

// Padded counter structure: Each instance is aligned to a separate cache line.
// This prevents false sharing because each thread writes to a distinct cache line.
// Size: 64 bytes (atomic) + 64 bytes (padding) + 64 bytes (data) = 192 bytes.
struct CounterPadded {
    alignas(CACHE_LINE_SIZE) std::atomic<long> value;
    alignas(CACHE_LINE_SIZE) char padding[CACHE_LINE_SIZE]; // Explicit padding to next cache line
    alignas(CACHE_LINE_SIZE) long data;

    CounterPadded() : value(0), data(0) {
        // Ensure padding is zero-initialized
        for(size_t i = 0; i < CACHE_LINE_SIZE; ++i) {
            padding[i] = 0;
        }
    }
};

static_assert(sizeof(CounterPadded) >= 192, "CounterPadded must be at least 192 bytes to ensure cache line separation");
static_assert(alignof(CounterPadded) >= CACHE_LINE_SIZE, "CounterPadded alignment must be at least cache line size");

#endif // COUNTER_PADDED_HPP