"""
Crowdfund smart contract (Algorand Python / algopy).

A creator launches a campaign with a funding goal (in microALGO) and a
deadline (UNIX timestamp). Backers opt in and pledge ALGO via a grouped
payment transaction.

* Goal reached by the deadline  -> creator can claim the funds.
* Goal missed by the deadline   -> each backer can claim a full refund.
"""

from algopy import (
    Account,
    ARC4Contract,
    Global,
    GlobalState,
    LocalState,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
)


class Crowdfund(ARC4Contract):
    def __init__(self) -> None:
        self.creator = GlobalState(Account)
        self.goal = GlobalState(UInt64)
        self.deadline = GlobalState(UInt64)
        self.raised = GlobalState(UInt64)
        self.claimed = GlobalState(bool)
        self.pledged = LocalState(UInt64)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    @arc4.abimethod(create="require")
    def create_campaign(self, goal: UInt64, deadline: UInt64) -> None:
        """Create a campaign with a goal (microALGO) and deadline (UNIX time)."""
        assert goal > 0, "goal must be positive"
        assert deadline > Global.latest_timestamp, "deadline must be in the future"
        self.creator.value = Txn.sender
        self.goal.value = goal
        self.deadline.value = deadline
        self.raised.value = UInt64(0)
        self.claimed.value = False

    @arc4.abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        """Backers opt in so the app can track their pledge."""
        self.pledged[Txn.sender] = UInt64(0)

    # ------------------------------------------------------------------ #
    # Backer actions
    # ------------------------------------------------------------------ #
    @arc4.abimethod
    def pledge(self, payment: gtxn.PaymentTransaction) -> UInt64:
        """Pledge ALGO. Must be grouped with a payment to the app account."""
        assert Global.latest_timestamp < self.deadline.value, "campaign has ended"
        assert payment.sender == Txn.sender, "payment must come from caller"
        assert (
            payment.receiver == Global.current_application_address
        ), "payment must go to the app"
        assert payment.amount > 0, "pledge must be positive"

        self.pledged[Txn.sender] = self.pledged[Txn.sender] + payment.amount
        self.raised.value += payment.amount
        return self.raised.value

    @arc4.abimethod
    def refund(self) -> UInt64:
        """Refund a backer's full pledge if the goal was not met."""
        assert Global.latest_timestamp >= self.deadline.value, "campaign still running"
        assert self.raised.value < self.goal.value, "goal was reached"

        amount = self.pledged[Txn.sender]
        assert amount > 0, "nothing to refund"
        self.pledged[Txn.sender] = UInt64(0)
        self.raised.value -= amount

        # fee=0: caller covers the inner-txn fee through fee pooling
        itxn.Payment(receiver=Txn.sender, amount=amount, fee=0).submit()
        return amount

    # ------------------------------------------------------------------ #
    # Creator actions
    # ------------------------------------------------------------------ #
    @arc4.abimethod
    def claim_funds(self) -> UInt64:
        """Creator withdraws the raised funds once the goal is met."""
        assert Txn.sender == self.creator.value, "only the creator can claim"
        assert Global.latest_timestamp >= self.deadline.value, "campaign still running"
        assert self.raised.value >= self.goal.value, "goal not reached"
        assert not self.claimed.value, "already claimed"

        self.claimed.value = True
        amount = self.raised.value
        itxn.Payment(receiver=self.creator.value, amount=amount, fee=0).submit()
        return amount

    # ------------------------------------------------------------------ #
    # Read-only helpers
    # ------------------------------------------------------------------ #
    @arc4.abimethod(readonly=True)
    def get_status(self) -> tuple[UInt64, UInt64, UInt64, bool]:
        """Return (goal, deadline, raised, claimed)."""
        return (
            self.goal.value,
            self.deadline.value,
            self.raised.value,
            self.claimed.value,
        )

    @arc4.abimethod(readonly=True)
    def get_pledge(self, backer: Account) -> UInt64:
        """Return how much a given backer has pledged."""
        return self.pledged[backer]
