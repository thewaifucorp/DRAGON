from enum import Enum


class Verdict(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
