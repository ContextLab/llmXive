#pragma once
#include <atomic>
#include <cstddef>

// Packed counter struct: 24 bytes total
// No padding between members, prone to false sharing
#pragma pack(push, 1)
struct CounterPacked {
    std::atomic<long> value;
    char padding[20]; // Ensure struct size is exactly 24 bytes if atomic is 8 bytes
    // In practice, std::atomic<long> is 8 bytes on 64-bit, so total is 28 bytes unless packed strictly
    // However, #pragma pack(1) forces 1-byte alignment.
    // Let's define it explicitly to ensure we hit the ~24-32 byte range typical of "packed" without cache line alignment.
    // To guarantee the specific size mentioned in the plan (24 bytes), we assume long is 8 bytes.
    // struct { atomic<long> (8) + char[16] } = 24 bytes.
    // We will use char[16] to make it exactly 24 bytes.
};
#pragma pack(pop)

// Re-defining for strict 24-byte size as per plan requirements
#pragma pack(push, 1)
struct CounterPackedStrict {
    std::atomic<long> value;
    char padding[16]; // 8 + 16 = 24 bytes
};
#pragma pack(pop)

using Counter = CounterPackedStrict;
