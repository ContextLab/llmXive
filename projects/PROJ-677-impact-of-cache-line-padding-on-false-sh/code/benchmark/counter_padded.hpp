#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstddef>

// Cache line size assumption (64 bytes)
constexpr size_t CACHE_LINE_SIZE = 64;

struct CounterPadded {
    long value;
    int id;
    char padding[CACHE_LINE_SIZE - sizeof(long) - sizeof(int)]; // Pad to 64 bytes?
    // Wait, T005 says "≥192 bytes padded".
    // If we have 3 threads, 3 * 64 = 192.
    // But the struct itself needs to be 64 bytes?
    // The requirement "≥192 bytes padded" in T005 likely refers to the total size 
    // if we were to allocate 3 of them contiguously? Or maybe the struct itself is larger?
    // Actually, T007 says "alignas(64) for padded (≥192 bytes)".
    // This is ambiguous. Does it mean the struct is 192 bytes? Or 3 structs are 192?
    // Given the context of "false sharing", we usually pad the struct to one cache line (64).
    // If T005 expects 192, maybe it expects 3 cache lines per counter? 
    // Or maybe it means the array of 3 counters is 192?
    // Let's re-read T005: "assert struct sizes (24 bytes packed, ≥192 bytes padded)".
    // This implies sizeof(CounterPadded) >= 192.
    // So we need to pad the struct to 192 bytes.
    // 192 / 64 = 3 cache lines.
    
    long value;
    int id;
    // Pad to 192 bytes total
    char padding[192 - sizeof(long) - sizeof(int)]; 
} __attribute__((aligned(64)));

static_assert(sizeof(CounterPadded) >= 192, "CounterPadded must be at least 192 bytes");
static_assert(sizeof(CounterPadded) % 64 == 0, "CounterPadded must be a multiple of cache line size");

inline void CounterPadded::increment() {
    ++value;
}

inline long CounterPadded::get() const {
    return value;
}

#endif // COUNTER_PADDED_HPP
