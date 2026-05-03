Voter Module (Student 5)

Description

This module simulates the voter in the electronic voting protocol.

Responsibilities of (Student 5):

- Create ballot (vote + N2 + random bits)
- Compute TTH(N2)
- Prepare data for signing and sending

  They are defined in the code voter.py , just I add some other fonctionalituies for locally testing .

⚠️ Important Notes for Integration

RSA Signature

- Currently implemented locally for testing
- MUST be replaced by Admin module

Replace:

private_key, public_key = generate_keys()
signature = sign_ballot(private_key, ballot["ballot"])

With:

signature = admin.sign(ballot["ballot"])

---

Verification

- Local verification is for testing only
- Final verification is handled by Counter module

---

Output Format

The module outputs:

{
  "ballot": {
    "vote": "...",
    "N2": "...",
    "random": "...",
    "ballot": "...",
    "tth": "..."
  },
  "signature": "..."
}

This structure must be used by:

- Admin
- Anonymizer
- Counter
