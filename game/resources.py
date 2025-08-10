from dataclasses import dataclass

@dataclass
class Resource:
    name: str
    amount: int = 0

    def add(self, qty: int):
        if qty > 0:
            self.amount += int(qty)

    def spend(self, qty: int) -> bool:
        if self.amount >= qty:
            self.amount -= qty
            return True
        return False

    def to_dict(self) -> dict:
        return {"name": self.name, "amount": self.amount}

    @staticmethod
    def from_dict(d: dict) -> 'Resource':
        return Resource(name=d.get("name", "Ore"), amount=d.get("amount", 0))

