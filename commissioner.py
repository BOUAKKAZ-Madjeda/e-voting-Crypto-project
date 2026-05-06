"""
=============================================================
  commissioner.py — The Voting Commissioner
=============================================================
  HOW IT WORKS:

  BEFORE ELECTION (run this ONCE before anyone votes):
    → Generate voter cards (N1 + N2) for each student
    → Store N1 and TTH(N2) in commissioner_data.json
    → Send each student their card via WhatsApp
    → Open the election when ready
    → List is CLOSED — no new voters can be added after opening

  DURING ELECTION:
    → voter.py calls verify_voter(N1, N2) automatically
    → If N1 not in list        → REJECTED
    → If N1 already voted      → REJECTED
    → If N2 wrong              → REJECTED

  DURING COUNTING:
    → counter.py calls verify_tth_n2(N2) automatically
=============================================================
"""
import json
import os
import random
import string
from tth import compute_tth


DATA_FILE = "commissioner_data.json"


def generate_code(length: int = 12) -> str:
    """Generate random 12-character alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"election_open": False, "voters": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# ── Functions called by voter.py and counter.py ───────────

def verify_voter(N1: str, N2: str) -> tuple:
    """
    Called by voter.py to verify N1 and N2.
    Returns (True, "OK") or (False, "reason")
    """
    data = load_data()

    if not data.get("election_open", False):
        return False, "Election is not open yet."

    if N1 not in data["voters"]:
        return False, f"N1 '{N1}' not found. You are not registered."

    if data["voters"][N1]["has_voted"]:
        return False, f"N1 '{N1}' already used. Double vote rejected."

    tth_provided = compute_tth(N2)
    tth_stored   = data["voters"][N1]["tth_n2"]

    if tth_provided != tth_stored:
        return False, "N2 is incorrect. Check your voter card."

    return True, "OK"


def invalidate_N1(N1: str):
    """Mark N1 as used. Called by voter.py after successful vote."""
    data = load_data()
    if N1 in data["voters"]:
        data["voters"][N1]["has_voted"] = True
        save_data(data)
        print(f"[COMMISSIONER] N1 '{N1}' invalidated — cannot vote again.")


def verify_tth_n2(N2: str) -> bool:
    """Check TTH(N2) is valid. Called by counter.py during counting."""
    data = load_data()
    tth = compute_tth(N2)
    for voter in data["voters"].values():
        if voter["tth_n2"] == tth:
            return True
    return False


# ── Commissioner interactive menu ─────────────────────────

def commissioner_menu():
    while True:
        data    = load_data()
        voters  = data.get("voters", {})
        is_open = data.get("election_open", False)
        voted   = sum(1 for v in voters.values() if v["has_voted"])

        print("\n" + "=" * 55)
        print("  COMMISSIONER — Electronic Voting System")
        print("=" * 55)
        print(f"  Registered voters : {len(voters)}")
        print(f"  Already voted     : {voted}")
        print(f"  Election status   : {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
        print("=" * 55)
        print("  1. Generate a voter card")
        print("  2. Open the election")
        print("  3. Close the election")
        print("  4. Show voter list")
        print("  5. Reset everything")
        print("  6. Exit")
        print("=" * 55)

        choice = input("Choose: ").strip()

        if choice == "1":
            if is_open:
                print("\n  ❌ Cannot add voters once election is open!")
                continue

            # Generate unique N1 and N2
            N1 = generate_code()
            while N1 in voters:
                N1 = generate_code()
            N2     = generate_code()
            tth_n2 = compute_tth(N2)

            data["voters"][N1] = {"tth_n2": tth_n2, "has_voted": False}
            save_data(data)

            print("\n  ┌─────────────────────────────────────┐")
            print("  │           VOTER CARD                │")
            print("  ├─────────────────────────────────────┤")
            print(f"  │  N1 : {N1}               │")
            print(f"  │  N2 : {N2}               │")
            print("  ├─────────────────────────────────────┤")
            print("  │  ⚠️  Send BOTH codes to the voter!  │")
            print("  └─────────────────────────────────────┘")
            print(f"\n  📱 Send via WhatsApp:")
            print(f"     N1 = {N1}")
            print(f"     N2 = {N2}")

        elif choice == "2":
            if len(voters) == 0:
                print("\n  ❌ No voters registered!")
                continue
            if is_open:
                print("\n  ⚠️  Already open.")
                continue
            confirm = input(f"\n  Open election for {len(voters)} voters? (yes/no): ").strip().lower()
            if confirm == "yes":
                data["election_open"] = True
                save_data(data)
                print("\n  ✅ Election is now OPEN!")
                print("  Students can now run voter.py")

        elif choice == "3":
            if not is_open:
                print("\n  ⚠️  Already closed.")
                continue
            confirm = input("\n  Close election? (yes/no): ").strip().lower()
            if confirm == "yes":
                data["election_open"] = False
                save_data(data)
                print("\n  🔴 Election CLOSED.")
                print("  Student 4 can now run counter.py")

        elif choice == "4":
            if not voters:
                print("\n  No voters yet.")
                continue
            print("\n  ┌──────────────────┬───────────────┐")
            print("  │       N1         │    Status     │")
            print("  ├──────────────────┼───────────────┤")
            for n1, info in voters.items():
                status = "✅ Voted" if info["has_voted"] else "⏳ Not yet"
                print(f"  │ {n1} │ {status:13} │")
            print("  └──────────────────┴───────────────┘")

        elif choice == "5":
            confirm = input("\n  ⚠️  Reset ALL data? (yes/no): ").strip().lower()
            if confirm == "yes":
                save_data({"election_open": False, "voters": {}})
                for f in ["ballots.json", "results.json", "admin_keys.json"]:
                    if os.path.exists(f):
                        os.remove(f)
                print("  ✅ Everything reset.")

        elif choice == "6":
            print("  Goodbye!")
            break
        else:
            print("  ❌ Invalid choice.")


if __name__ == "__main__":
    commissioner_menu()
