from dataclasses import dataclass, field
import random

TRAITS = {
    "Overzealous": {"drive_xp_mult": 1.5, "str_xp_mult": 0.75},
    "Lazy":       {"drive_xp_mult": 0.75, "str_xp_mult": 1.5},
    "Efficient":  {"drive_xp_mult": 1.25, "str_xp_mult": 1.25},
    "Clumsy":     {"str_xp_mult": 0.75},
    "Lucky":      {"bonus_ore_chance": 0.05},
    "Stalwart":   {"str_xp_mult": 1.1, "drive_xp_mult": 1.1},
}

SPECIALIZE_LEVEL = 5

SYLLABLES = [
    "zor", "vik", "ka", "ron", "thu", "mar", "xel", "tri", "pha", "gon",
    "qua", "len", "shi", "bor", "nek", "vol", "dra", "ula", "syl", "orn"
]

def make_name():
    count = random.choice([2, 3])
    return "".join(random.choice(SYLLABLES) for _ in range(count)).capitalize()

@dataclass
class Entity:
    name: str = field(default_factory=make_name)
    strength: int = field(default_factory=lambda: random.randint(1, 3))
    drive: int = field(default_factory=lambda: random.randint(0, 2))
    trait_name: str = field(default_factory=lambda: random.choice(list(TRAITS.keys())))
    risk_aversion: float = field(default_factory=lambda: random.uniform(0.3, 0.9))
    str_xp: float = 0.0
    dri_xp: float = 0.0
    str_level: int = 0
    dri_level: int = 0
    specialization: str | None = None
    ticks_survived: int = 0

    def trait(self) -> dict:
        return TRAITS.get(self.trait_name, {})

    def xp_threshold(self, level: int) -> int:
        return 10 * (level + 1)

    def manual_mine(self, resource) -> int:
        bonus = 1 if self.specialization == "Master Miner" else 0
        ore_gained = self.strength + bonus
        if "bonus_ore_chance" in self.trait() and random.random() < self.trait()["bonus_ore_chance"]:
            ore_gained += 1
        resource.add(ore_gained)
        self.str_xp += 1.0 * self.trait().get("str_xp_mult", 1.0)
        self._check_levelups()
        return ore_gained

    def auto_mine(self, resource) -> int:
        bonus = 1 if self.specialization == "Automation Expert" else 0
        ore_gained = self.drive + bonus
        if "bonus_ore_chance" in self.trait() and random.random() < self.trait()["bonus_ore_chance"]:
            ore_gained += 1
        resource.add(ore_gained)
        self.dri_xp += 1.0 * self.trait().get("drive_xp_mult", 1.0)
        self._check_levelups()
        return ore_gained

    def _check_levelups(self):
        while self.str_xp >= self.xp_threshold(self.str_level):
            self.str_xp -= self.xp_threshold(self.str_level)
            self.str_level += 1
            self.strength += 1
            if self.specialization is None and self.str_level >= SPECIALIZE_LEVEL:
                self.specialization = "Master Miner"
        while self.dri_xp >= self.xp_threshold(self.dri_level):
            self.dri_xp -= self.xp_threshold(self.dri_level)
            self.dri_level += 1
            self.drive += 1
            if self.specialization is None and self.dri_level >= SPECIALIZE_LEVEL:
                self.specialization = "Automation Expert"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "strength": self.strength,
            "drive": self.drive,
            "trait_name": self.trait_name,
            "risk_aversion": self.risk_aversion,
            "str_xp": self.str_xp,
            "dri_xp": self.dri_xp,
            "str_level": self.str_level,
            "dri_level": self.dri_level,
            "specialization": self.specialization,
            "ticks_survived": self.ticks_survived,
        }

    @staticmethod
    def from_dict(d: dict) -> 'Entity':
        return Entity(
            name=d.get("name", make_name()),
            strength=d.get("strength", 1),
            drive=d.get("drive", 0),
            trait_name=d.get("trait_name", random.choice(list(TRAITS.keys()))),
            risk_aversion=d.get("risk_aversion", random.uniform(0.3, 0.9)),
            str_xp=d.get("str_xp", 0.0),
            dri_xp=d.get("dri_xp", 0.0),
            str_level=d.get("str_level", 0),
            dri_level=d.get("dri_level", 0),
            specialization=d.get("specialization"),
            ticks_survived=d.get("ticks_survived", 0),
        )

