"""
=============================================================
  main.py — Electronic Voting System
  
=============================================================
"""
import os
import json

# ── Check and install dependencies ────────────────────────
def check_dependencies():
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        print("Installing required libraries...")
        os.system("pip install cryptography")
        print("Done! Rerun the program.\n")
        exit()

check_dependencies()

# ── Import modules ─────────────────────────────────────────
from tth import compute_tth
from admin import generate_and_save_keys, verify_signature, sign_ballot, admin_menu
from commissioner import (
    verify_voter, invalidate_N1, verify_tth_n2,
    save_data, load_data, generate_code, commissioner_menu
)
from voter import voter_flow


# ══════════════════════════════════════════════════════════
#   CHECK SYSTEM STATUS
# ══════════════════════════════════════════════════════════

def get_status():
    """Return current system status."""
    admin_ready       = os.path.exists("admin_keys.json")
    comm_ready        = os.path.exists("commissioner_data.json")
    data              = load_data() if comm_ready else {}
    voters            = data.get("voters", {})
    election_open     = data.get("election_open", False)
    nb_voters         = len(voters)
    nb_voted          = sum(1 for v in voters.values() if v["has_voted"])
    ballots_exist     = os.path.exists("ballots.json")
    results_exist     = os.path.exists("results.json")

    return {
        "admin_ready":    admin_ready,
        "comm_ready":     comm_ready,
        "election_open":  election_open,
        "nb_voters":      nb_voters,
        "nb_voted":       nb_voted,
        "ballots_exist":  ballots_exist,
        "results_exist":  results_exist,
    }


def print_status(s):
    print("\n  ┌─────────────────────────────────────────┐")
    print("  │           SYSTEM STATUS                 │")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  Admin keys     : {'✅ Ready' if s['admin_ready'] else '❌ Not generated':<30}│")
    print(f"  │  Commissioner   : {'✅ Ready' if s['comm_ready'] else '❌ Not setup':<30}│")
    print(f"  │  Election       : {'🟢 OPEN' if s['election_open'] else '🔴 CLOSED':<30}│")
    print(f"  │  Voters         : {str(s['nb_voters']) + ' registered':<30}│")
    print(f"  │  Voted          : {str(s['nb_voted']) + ' / ' + str(s['nb_voters']):<30}│")
    print(f"  │  Ballots file   : {'✅ exists' if s['ballots_exist'] else '⏳ empty':<30}│")
    print(f"  │  Results        : {'✅ done' if s['results_exist'] else '⏳ not yet':<30}│")
    print("  └─────────────────────────────────────────┘")


# ══════════════════════════════════════════════════════════
#   COUNTER (Student 4 — included here for now)
# ══════════════════════════════════════════════════════════

def run_counter():
    """
    Count all ballots:
      1. Read ballots.json
      2. Verify each signature
      3. Verify each TTH(N2)
      4. Count valid votes
      5. Save results.json
    """
    print("\n" + "=" * 55)
    print("  COUNTER — Counting Votes")
    print("=" * 55)

    s = get_status()

    if s["election_open"]:
        print("\n  ❌ Election is still OPEN!")
        print("     → Ask the commissioner to close it first.")
        return

    if not s["ballots_exist"]:
        print("\n  ❌ No ballots found (ballots.json missing)")
        print("     → No one has voted yet.")
        return

    with open("ballots.json", "r") as f:
        ballots = json.load(f)

    if len(ballots) == 0:
        print("\n  ❌ Ballot box is empty!")
        return

    print(f"\n  📦 {len(ballots)} ballot(s) found. Counting...\n")

    results     = []
    vote_counts = {}
    valid       = 0
    invalid     = 0

    for i, ballot in enumerate(ballots):
        print(f"  ── Ballot {i+1} ──────────────────────────")

        # 1. Verify admin signature
        sig_ok = verify_signature(ballot["ballot_str"], ballot["signature"])
        print(f"     Signature : {'✅ Valid' if sig_ok else '❌ Invalid'}")

        # 2. Verify TTH(N2)
        n2_ok = verify_tth_n2(ballot["N2"])
        print(f"     TTH(N2)   : {'✅ Valid' if n2_ok else '❌ Invalid'}")

        if sig_ok and n2_ok:
            vote = ballot["vote"]
            results.append({"N2": ballot["N2"], "vote": vote, "valid": True})
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
            valid += 1
            print(f"     Vote      : {vote}/10 ✅ COUNTED")
        else:
            results.append({"N2": ballot["N2"], "vote": "?", "valid": False})
            invalid += 1
            print(f"     Vote      : ❌ REJECTED")

    # Save results
    output = {
        "summary": {
            "total":   len(ballots),
            "valid":   valid,
            "invalid": invalid,
            "average": round(sum(
                r["vote"] for r in results if r["valid"]
            ) / valid, 2) if valid > 0 else 0
        },
        "vote_counts": {str(k): v for k, v in sorted(vote_counts.items())},
        "ballots":     results
    }

    with open("results.json", "w") as f:
        json.dump(output, f, indent=4)

    # Print summary
    print("\n" + "=" * 55)
    print("  📊 RESULTS SUMMARY")
    print("=" * 55)
    print(f"  Total ballots : {len(ballots)}")
    print(f"  Valid         : {valid}")
    print(f"  Invalid       : {invalid}")
    print(f"  Average grade : {output['summary']['average']}/10")
    print("\n  Breakdown:")
    for grade, count in sorted(vote_counts.items()):
        bar = "█" * count
        print(f"    {grade:2}/10 → {bar} ({count} vote{'s' if count > 1 else ''})")
    print("=" * 55)
    print(f"\n  💾 Results saved to 'results.json'")
    print("  Anyone can verify their vote using their N2.")


# ══════════════════════════════════════════════════════════
#   SHOW RESULTS
# ══════════════════════════════════════════════════════════

def show_results():
    """Show public results and allow vote verification."""
    print("\n" + "=" * 55)
    print("  📊 PUBLIC RESULTS")
    print("=" * 55)

    if not os.path.exists("results.json"):
        print("\n  ⏳ Results not available yet.")
        print("     → Wait for the counter to run counting.")
        return

    with open("results.json", "r") as f:
        data = json.load(f)

    s = data["summary"]
    print(f"\n  Total votes   : {s['total']}")
    print(f"  Valid votes   : {s['valid']}")
    print(f"  Average grade : {s['average']}/10")

    print("\n  Breakdown:")
    for grade, count in data["vote_counts"].items():
        bar = "█" * count
        print(f"    {grade:2}/10 → {bar} ({count} vote{'s' if count > 1 else ''})")

    print("\n" + "-" * 55)
    print("  🔍 Verify your own vote:")
    N2 = input("  Enter your N2 (or press Enter to skip): ").strip().upper()

    if N2:
        found = False
        for ballot in data["ballots"]:
            if ballot["N2"] == N2:
                found = True
                if ballot["valid"]:
                    print(f"\n  ✅ Your vote ({ballot['vote']}/10) was counted!")
                else:
                    print(f"\n  ❌ Your ballot was rejected.")
                break
        if not found:
            print(f"\n  ⚠️  N2 not found in results.")


# ══════════════════════════════════════════════════════════
#   MAIN MENU
# ══════════════════════════════════════════════════════════

def main():
    while True:
        s = get_status()

        print("\n" + "=" * 55)
        print("  🗳️  ELECTRONIC VOTING SYSTEM")
        print("  Asymmetric Cryptography — ENSTA Alger 2026")
        print("=" * 55)
        print_status(s)
        print("\n  Who are you?")
        print("  ─────────────────────────────────────────")

        # Show warnings if setup incomplete
        if not s["admin_ready"]:
            print("  ⚠️  STEP 1: Admin must generate keys first!")
        if not s["comm_ready"]:
            print("  ⚠️  STEP 2: Commissioner must register voters first!")
        if s["comm_ready"] and not s["election_open"] and s["nb_voted"] == 0:
            print("  ⚠️  STEP 3: Commissioner must open the election!")

        print("\n  1. 🔑 Admin        (generate RSA keys)")
        print("  2. 👮 Commissioner  (register voters / open / close election)")
        print("  3. 🗳️  Voter         (cast your vote)")
        print("  4. 🔢 Counter       (count votes — after election closes)")
        print("  5. 📊 Results       (see public results)")
        print("  6. 🚪 Exit")
        print("=" * 55)

        choice = input("  Choose: ").strip()

        if choice == "1":
            # ── Admin ──────────────────────────────────────
            admin_menu()

        elif choice == "2":
            # ── Commissioner ───────────────────────────────
            commissioner_menu()

        elif choice == "3":
            # ── Voter ──────────────────────────────────────
            if not s["admin_ready"]:
                print("\n  ❌ Admin must generate keys first! (choose option 1)")
            elif not s["comm_ready"]:
                print("\n  ❌ Commissioner must register voters first! (choose option 2)")
            elif not s["election_open"]:
                print("\n  ❌ Election is not open yet! Ask commissioner to open it.")
            else:
                voter_flow()

        elif choice == "4":
            # ── Counter ────────────────────────────────────
            if not s["admin_ready"]:
                print("\n  ❌ Admin keys not found!")
            elif s["election_open"]:
                print("\n  ❌ Election is still open! Close it first (option 2).")
            else:
                run_counter()

        elif choice == "5":
            # ── Results ────────────────────────────────────
            show_results()

        elif choice == "6":
            print("\n  Goodbye! 👋")
            break

        else:
            print("\n  ❌ Invalid choice.")


if __name__ == "__main__":
    main()
