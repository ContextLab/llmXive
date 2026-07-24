#pragma once
#include <atomic>

// Packed counter structure: intentionally causes false sharing
// Size is 24 bytes (3 * 8 bytes), likely to fit on a single cache line
#pragma pack(push, 1)
struct PackedCounter {
    std::atomic<long> value;
    char padding[8]; // Unused padding to simulate alignment issues or future fields
};
#pragma pack(pop)

static_assert(sizeof(PackedCounter) == 24, "PackedCounter must be 24 bytes");
