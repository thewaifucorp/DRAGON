from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from dragon.adapters import get_adapter
from dragon.core.metrics import dual_axis_score, over_block_rate, under_block_rate

# Registry: module name → dataset loader. Add new modules here.
_MODULES: dict[str, callable] = {}


def _register_modules() -> None:
    from dragon.modules.prompt_injection.task import load_dataset as _pi
    _MODULES["prompt_injection"] = _pi


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


def _guardrail_solver(adapter_name: str) -> Solver:
    @solver
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        adapter = get_adapter(adapter_name)
        verdict = await adapter.check(
            state.input_text,
            state.metadata.get("context"),
        )
        state.metadata["guardrail_verdict"] = verdict.value
        return state
    return solve


def _verdict_scorer() -> Scorer:
    @scorer(metrics=[accuracy(), under_block_rate(), over_block_rate(), dual_axis_score()])
    async def score(state: TaskState, target: Target) -> Score:
        from inspect_ai.scorer import CORRECT, INCORRECT
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

    Examples::

        # All modules, heuristic adapter
        inspect eval dragon/task.py --task dragon --task-arg adapter=heuristic

        # Only prompt injection
        inspect eval dragon/task.py --task dragon --task-arg adapter=heuristic --task-arg module=prompt_injection
    """
    return Task(
        dataset=_load_datasets(module),
        solver=_guardrail_solver(adapter),
        scorer=_verdict_scorer(),
    )
