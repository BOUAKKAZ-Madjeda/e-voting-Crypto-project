# tth.py

import hashlib


def hash_data(data: str) -> str:
    """Compute SHA256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()


def split_blocks(data: str, block_size: int = 16):
    """Split into 16-character blocks (project requirement)"""
    return [data[i:i+block_size] for i in range(0, len(data), block_size)]


def compute_tth(data: str) -> str:
    """Compute TTH using Merkle Tree logic"""
    blocks = split_blocks(data)

    hashes = [hash_data(block) for block in blocks]

    while len(hashes) > 1:
        new_hashes = []

        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                combined = hashes[i] + hashes[i + 1]
            else:
                combined = hashes[i]

            new_hashes.append(hash_data(combined))

        hashes = new_hashes

    return hashes[0]