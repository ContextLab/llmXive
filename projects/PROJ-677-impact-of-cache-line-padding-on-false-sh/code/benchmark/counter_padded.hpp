#ifndef COUNTER_PADDED_HPP
#define COUNTER_PADDED_HPP

#include <cstdint>
#include <cstddef>

// Cache line size constant (typically 64 bytes on modern x86-64)
constexpr size_t CACHE_LINE_SIZE = 64;

// Padded counter structure - each counter is aligned to cache line boundary
// This prevents false sharing because each thread writes to a different cache line
struct alignas(CACHE_LINE_SIZE) CounterStruct {
    int64_t value;      // 8 bytes
    int32_t thread_id;  // 4 bytes
    // Remaining 56 bytes are padding to reach 64 bytes total
    // The alignas attribute ensures the struct itself is 64-byte aligned
    // and each instance in an array will be 64 bytes apart
};

static_assert(sizeof(CounterStruct) >= CACHE_LINE_SIZE, "CounterStruct should be at least 64 bytes when padded");

#endif // COUNTER_PADDED_HPP