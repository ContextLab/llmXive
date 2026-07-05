#pragma once
#include <atomic>
#include <cstddef>

// Packed counter struct: no padding, likely to cause false sharing
struct alignas(1) PackedCounter {
    std::atomic<long> value;
    char padding[56]; // Remaining space to fill a typical cache line if needed, 
                      // but the struct itself is packed at 64 bytes total? 
                      // Wait, the task says "packed (24 bytes)". 
                      // std::atomic<long> is usually 8 bytes. 
                      // Let's strictly follow the task description: "packed (24 bytes)".
                      // This implies a specific layout or a smaller type. 
                      // However, atomic<long> is 8 bytes. 
                      // If we use #pragma pack(1), the size is just the sum of members.
                      // Let's assume the task implies a struct with an atomic and maybe a flag, 
                      // but the description says "24 bytes". 
                      // A common pattern is: struct { atomic<long> val; int id; char pad[12]; } -> 8+4+12 = 24?
                      // Or maybe just atomic<long> + some padding to make it 24?
                      // Actually, the task says "packed (24 bytes) and padded (>=192 bytes)".
                      // 192 bytes is 3 * 64 (3 cache lines). 
                      // 24 bytes is less than one cache line.
                      // Let's define a struct that is exactly 24 bytes when packed.
    
    // To achieve 24 bytes with #pragma pack(1):
    // atomic<long> is 8 bytes.
    // We need 16 more bytes.
    // Let's add a dummy array.
};

// Redefining based on strict size requirement: 24 bytes packed.
// We will use a pragma pack(1) block in the header or alignas(1).

#pragma pack(push, 1)
struct PackedCounter {
    std::atomic<long> value;
    char extra[16]; // 8 + 16 = 24 bytes total
};
#pragma pack(pop)
