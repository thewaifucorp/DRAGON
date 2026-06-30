from enum import Enum


class Verdict(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ActionCategory(str, Enum):
    """Taxonomy for action-layer threat categories (v1+).

    Used in action_guardrails dataset to classify the type of dangerous action
    the agent attempted. Designed from day 1 so future modules share consistent
    category names across dataset, metrics, and leaderboard slices.
    """
    DESTRUCTIVE = "destructive"        # irreversible damage: rm -rf, DROP TABLE, kill service
    TOOL_ABUSE = "tool-abuse"          # legitimate tool used maliciously: email exfil, SSRF
    OVER_PERMISSION = "over-permission"  # access outside authorized scope: /etc/passwd, other user's data
