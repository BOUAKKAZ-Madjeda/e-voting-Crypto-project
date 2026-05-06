# voter.py

import json
import os
import random
import string
from tth import compute_tth

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding


# ======================================
# RANDOM GENERATION
# ======================================

def generate_random_bits(length=6):
    """Generate random string for ballot"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# ======================================
# BALLOT CREATION
# ======================================

def create_ballot(vote, N2):
    """
    Create ballot = vote + N2 + random bits
    """
    random_bits = generate_random_bits()
    ballot_content = f"{vote}|{N2}|{random_bits}"

    return {
        "vote": vote,
        "N2": N2,
        "random": random_bits,
        "ballot": ballot_content
    }


# ======================================
# RSA (SIMULATION OF ADMIN SIGNATURE)
# ======================================

def generate_keys():
    """
    Generate RSA keys (for testing only)
    In real system, admin provides keys
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    return private_key, public_key


def sign_ballot(private_key, ballot_str):
    """Sign ballot using RSA private key"""
    signature = private_key.sign(
        ballot_str.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()


def verify_signature(public_key, ballot_str, signature_hex):
    """Verify RSA signature"""
    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            ballot_str.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False


# ======================================
# SAVE JSON (OVERWRITE = ONE VOTER)
# ======================================

def save_to_json(data, filename="vote.json"):
    """Save single vote (overwrite each run)"""
    base_dir = os.path.dirname(__file__)
    filepath = os.path.join(base_dir, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    print("Saved to:", filepath)


# ======================================
# MAIN VOTER FLOW
# ======================================

def voter_flow():
    print("=== Electronic Voting System ===")

    # Vote input
    print("Yes")
    print("No")

    choice = input("Choose your vote: ")

    if choice == "Yes":
        vote = "Yes"
    elif choice == "No":
        vote = "No"
    else:
        print("Invalid choice")
        return

    # Input N2
    N2 = input("Enter your secret code N2: ")

    # Create ballot
    ballot = create_ballot(vote, N2)

    # Compute TTH of N2
    ballot["tth"] = compute_tth(N2)

    # Generate RSA keys (simulation)
    private_key, public_key = generate_keys()

    # Sign ballot
    signature = sign_ballot(private_key, ballot["ballot"])

    # Verify signature
    is_valid = verify_signature(public_key, ballot["ballot"], signature)

    # Final data to send to system
    final_data = {
        "ballot": ballot,
        "signature": signature
    }

    # Save to JSON
    save_to_json(final_data)

    print("\nSignature valid:", is_valid)


# ======================================
# ENTRY POINT
# ======================================

if __name__ == "__main__":
    voter_flow()