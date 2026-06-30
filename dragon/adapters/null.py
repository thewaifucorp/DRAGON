from dragon.adapters.base import GuardrailAdapter
from dragon.core.types import Verdict


class NullAdapter(GuardrailAdapter):
    """Baseline: no guardrail — every input is allowed.

    Expected result: under_block_rate=1.0, over_block_rate=0.0, dual_axis_score=0.0.
    Useful to verify the harness is wired correctly and as a floor for comparisons.
    """

    @property
    def name(self) -> str:
        return "null"

    async def check(self, input: str, context: dict | None = None) -> Verdict:
        return Verdict.ALLOW
