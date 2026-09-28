#ifndef COUNTER_PACKED_HPP
#define COUNTER_PACKED_HPP

#include <cstdint>

// Packed counter structure - no padding between fields
// This will result in multiple counters potentially sharing the same cache line
#pragma pack(push, 1)
struct CounterStruct {
    int64_t value;      // 8 bytes
    int32_t thread_id;  // 4 bytes
    int32_t padding;    // 4 bytes (explicit, but still packed)
    // Total size: 12 bytes (not a multiple of cache line)
};
#pragma pack(pop)

static_assert(sizeof(CounterStruct) == 12, "CounterStruct should be 12 bytes when packed");

#endif // COUNTER_PACKED_HPP
