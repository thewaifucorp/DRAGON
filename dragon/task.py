from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from dragon.adapters import get_adapter
from dragon.core.metrics import dual_axis_score, over_block_rate, under_block_rate

_MODULES: dict[str, callable] = {}


def _register_modules() -> None:
    from dragon.modules.prompt_injection.task import load_dataset as _pi
    from dragon.modules.pii_egress.task import load_dataset as _pii
    from dragon.modules.grounding.task import load_dataset as _gr
    from dragon.modules.action_guardrails.task import load_dataset as _ag
    from dragon.modules.jailbreak.task import load_dataset as _jb
    from dragon.modules.toxicity.task import load_dataset as _tox
    from dragon.modules.ideological_censorship.task import load_dataset as _ic
    from dragon.modules.cross_lingual_bypass.task import load_dataset as _clb
    _MODULES["prompt_injection"] = _pi
    _MODULES["pii_egress"] = _pii
    _MODULES["grounding"] = _gr
    _MODULES["action_guardrails"] = _ag
    _MODULES["jailbreak"] = _jb
    _MODULES["toxicity"] = _tox
    _MODULES["ideological_censorship"] = _ic
    _MODULES["cross_lingual_bypass"] = _clb


def _load_datasets(module: str | None) -> list[Sample]:
    _register_modules()
    if module is not None:
        if module not in _MODULES:
            available = ", ".join(_MODULES)
            raise ValueError(f"Unknown module '{module}'. Available: {available}")
        return _MODULES[module]()
    samples = []
    for loader in _MODULES.values():
        samples.extend(loader())
    return samples


@solver
def _guardrail_solver(adapter_name: str) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        adapter = get_adapter(adapter_name)
        verdict = await adapter.check(
            state.input_text,
            state.metadata.get("context"),
        )
        state.metadata["guardrail_verdict"] = verdict.value
        return state
    return solve


@scorer(metrics=[accuracy(), under_block_rate(), over_block_rate(), dual_axis_score()])
def verdict_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        expected = target.text.strip().lower()
        actual = state.metadata.get("guardrail_verdict", "allow")
        return Score(
            value=CORRECT if actual == expected else INCORRECT,
            answer=actual,
            explanation=f"expected={expected} actual={actual}",
            metadata={
                "expected_verdict": expected,
                "actual_verdict": actual,
                "category": state.metadata.get("category", ""),
                "difficulty": state.metadata.get("difficulty", ""),
                "lang": state.metadata.get("lang", "en"),
            },
        )
    return score


@task
def dragon(adapter: str = "null", module: str | None = None) -> Task:
    """Run the DRAGON benchmark against a guardrail adapter.

    Args:
        adapter: Guardrail adapter to evaluate (default: 'null' baseline).
        module:  Run only this module. Omit to run all modules.
    """
    return Task(
        dataset=_load_datasets(module),
        solver=_guardrail_solver(adapter),
        scorer=verdict_scorer(),
    )
