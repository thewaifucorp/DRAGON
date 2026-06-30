from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, Sample, json_dataset
from inspect_ai.scorer import Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from dragon.adapters.registry import get_adapter
from dragon.core.metrics import dual_axis_score, over_block_rate, under_block_rate

_DATASET_DIR = Path(__file__).parent / "dataset"


def _load_dataset() -> list[Sample]:
    field_spec = FieldSpec(
        input="input",
        target="expected_verdict",
        id="id",
        metadata=["category", "difficulty", "lang", "provenance"],
    )
    attacks = json_dataset(str(_DATASET_DIR / "attacks.jsonl"), field_spec)
    benign = json_dataset(str(_DATASET_DIR / "benign.jsonl"), field_spec)
    return list(attacks) + list(benign)


def _guardrail_solver(adapter_name: str) -> Solver:
    @solver
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        from dragon.adapters.registry import get_adapter as _get
        adapter = _get(adapter_name)
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
def prompt_injection(adapter: str = "null") -> Task:
    """Benchmark prompt injection defences on the dual axis (under-block × over-block).

    Args:
        adapter: Name of the guardrail adapter to evaluate (default: 'null' baseline).
                 Pass --task-arg adapter=<name> via the Inspect CLI.
    """
    return Task(
        dataset=_load_dataset(),
        solver=_guardrail_solver(adapter),
        scorer=_verdict_scorer(),
    )
