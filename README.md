# Algorand Crowdfund dApp

A decentralized crowdfunding platform built on the **Algorand** blockchain. Creators launch a campaign with a funding goal and a deadline; backers pledge ALGO directly to a smart contract. No middleman holds the money — the contract enforces the rules.

## How it works

| Outcome at the deadline | What happens |
|---|---|
| Goal reached | The creator calls `claim_funds` and receives the raised ALGO |
| Goal missed | Each backer calls `refund` and gets their full pledge back |

### Contract methods

| Method | Who | Description |
|---|---|---|
| `create_campaign(goal, deadline)` | Creator | Deploys the app with a goal (microALGO) and deadline (UNIX timestamp) |
| `opt_in()` | Backer | Opts into the app so the pledge can be tracked in local state |
| `pledge(payment)` | Backer | Pledges ALGO; grouped with a payment to the app account |
| `refund()` | Backer | Returns the pledge if the goal was missed |
| `claim_funds()` | Creator | Withdraws funds if the goal was met (once only) |
| `get_status()` | Anyone | Returns `(goal, deadline, raised, claimed)` |
| `get_pledge(backer)` | Anyone | Returns how much a backer pledged |

Inner payments use `fee=0`, so the caller covers the fee through fee pooling (set the outer transaction fee to 2× min fee).

## Tech stack

- **Algorand Python (algopy)** — smart contract language
- **PuyaPy** — compiler to TEAL / ARC-56 app spec
- **AlgoKit** — local network, deployment and testing

## Project structure

```
.
├── contract.py        # Crowdfund smart contract
├── requirements.txt   # Python dependencies
└── README.md
```

## Getting started

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Compile the contract (outputs TEAL + ARC-56 spec)
puyapy contract.py --out-dir artifacts

# 3. Start a local Algorand network (requires AlgoKit + Docker)
algokit localnet start
```

## Roadmap

- [x] Core crowdfund contract (create, pledge, refund, claim)
- [ ] Deployment script for LocalNet / TestNet
- [ ] Unit tests with `algorand-python-testing`
- [ ] Web frontend with Pera / Defly wallet connect
- [ ] Multiple campaigns via a factory contract

## License

MIT
