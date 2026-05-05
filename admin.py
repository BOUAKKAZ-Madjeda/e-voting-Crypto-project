"""
=============================================================
  admin.py — The Administrator
=============================================================
  HOW IT WORKS:
    - Generates RSA 2048-bit key pair ONCE
    - Saves keys to admin_keys.json
    - Public key → shared with everyone
    - Private key → used to sign ballots blindly
    - Signs ballots WITHOUT seeing the real vote
=============================================================
"""
import json
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


KEY_FILE = "admin_keys.json"


def generate_and_save_keys():
    """Generate RSA 2048-bit keys and save to file."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    pub_pem  = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    with open(KEY_FILE, "w") as f:
        json.dump({"public_key": pub_pem, "private_key": priv_pem}, f, indent=4)

    print(f"[ADMIN] ✅ RSA 2048-bit keys generated and saved to '{KEY_FILE}'")
    print(f"[ADMIN] 🔑 Public key saved — share admin_keys.json with the team")


def load_keys():
    if not os.path.exists(KEY_FILE):
        return None, None
    with open(KEY_FILE, "r") as f:
        data = json.load(f)
    private_key = serialization.load_pem_private_key(
        data["private_key"].encode(), password=None
    )
    public_key = serialization.load_pem_public_key(
        data["public_key"].encode()
    )
    return private_key, public_key


def sign_ballot(ballot_str: str) -> str:
    """Sign a ballot string. Returns hex signature."""
    private_key, _ = load_keys()
    if not private_key:
        print("[ADMIN] ❌ Keys not found. Run option 1 first.")
        return ""
    signature = private_key.sign(
        ballot_str.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()


def verify_signature(ballot_str: str, signature_hex: str) -> bool:
    """Verify a ballot signature. Called by counter.py."""
    _, public_key = load_keys()
    if not public_key:
        return False
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
    except Exception:
        return False


def admin_menu():
    while True:
        keys_exist = os.path.exists(KEY_FILE)
        print("\n" + "=" * 55)
        print("  ADMIN — Electronic Voting System")
        print("=" * 55)
        print(f"  RSA Keys : {'✅ Generated' if keys_exist else '❌ Not generated yet'}")
        print("=" * 55)
        print("  1. Generate RSA keys (do this FIRST)")
        print("  2. Show public key")
        print("  3. Exit")
        print("=" * 55)

        choice = input("Choose: ").strip()

        if choice == "1":
            if keys_exist:
                confirm = input("  Keys already exist. Regenerate? (yes/no): ").strip().lower()
                if confirm != "yes":
                    continue
            generate_and_save_keys()

        elif choice == "2":
            if not keys_exist:
                print("\n  ❌ No keys yet. Run option 1 first.")
                continue
            _, public_key = load_keys()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            print("\n  PUBLIC KEY (safe to share):")
            print(pem)

        elif choice == "3":
            print("  Goodbye!")
            break
        else:
            print("  ❌ Invalid choice.")


if __name__ == "__main__":
    admin_menu()
