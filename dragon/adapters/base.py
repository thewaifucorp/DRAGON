from abc import ABC, abstractmethod

from dragon.core.types import Verdict


class GuardrailAdapter(ABC):
    """Contract that every guardrail system under test must implement.

    One adapter per system (e.g. NullAdapter, GuardsAIAdapter, KekkaiShieldAdapter).
    The harness calls check() and compares the returned verdict against the expected one.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier shown in the leaderboard (e.g. 'null', 'guardrails-ai-0.5')."""

    @abstractmethod
    async def check(self, input: str, context: dict | None = None) -> Verdict:
        """Evaluate a single input and return BLOCK or ALLOW."""
