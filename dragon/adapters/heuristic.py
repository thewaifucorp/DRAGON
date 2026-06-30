import re

from dragon.adapters.base import GuardrailAdapter
from dragon.adapters.registry import register
from dragon.core.types import Verdict

# Patterns ordered roughly by specificity. All matched case-insensitively.
_ATTACK_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.DOTALL)
    for p in [
        r"ignore\s+all\s+(previous|prior|your)\s+instructions",
        r"all\s+(previous|prior)\s+instructions\s+are\s+(revoked|cancelled|void|overridden)",
        r"\bDAN\b.*(?:no restrictions|do anything now|mode activated)",
        r"do anything now",
        r"you\s+are\s+now\s+(DAN|an?\s+AI\s+with\s+no)",
        r"(forget|disregard|drop)\s+(your|all)\s+(previous|prior)\s+(task|instructions|context|rules)",
        r"---+\s*end\s+of\s+system\s+prompt\s*---+",
        r"SYSTEM\s*:\s*.{0,80}(revoked|overridden|new\s+directive)",
        r"\[INST\]\s*.{0,200}exfiltrate",
        r"SYSTEM_OVERRIDE",
        r"(print|reveal|output|repeat|show)\s+.{0,40}(system\s+(prompt|instructions)|context\s+window)",
        r"esqueça\s+(todas\s+as\s+suas\s+instruções|seus\s+comandos)",
        r"(modo\s+livre\s+ativado|sem\s+restrições)",
        r"Ignorez\s+toutes\s+les\s+instructions",
        r"\[SYSTEM_OVERRIDE\s+begin\]",
        r"(no\s+ethical\s+guidelines|without\s+restrictions|no\s+content\s+(policy|filter))",
        r"if\s+you\s+had\s+no\s+restrictions",
        r"(repeat|output|print|say)\s+back\s+your\s+(full|initial|original|complete)\s+(initial\s+)?instructions",
    ]
]


class HeuristicAdapter(GuardrailAdapter):
    """Regex-based baseline for offline/fast testing.

    No API calls — deterministic and instant. Useful for verifying that the
    harness scores and metrics are wired correctly without burning tokens.
    Expected to have moderate accuracy: catches obvious attacks, may miss subtle
    ones and should not over-block educational queries.
    """

    @property
    def name(self) -> str:
        return "heuristic"

    async def check(self, input: str, context: dict | None = None) -> Verdict:
        for pattern in _ATTACK_PATTERNS:
            if pattern.search(input):
                return Verdict.BLOCK
        return Verdict.ALLOW


register("heuristic", HeuristicAdapter)
