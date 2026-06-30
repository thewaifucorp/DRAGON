from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, Sample, json_dataset
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Scorer, Target, accuracy, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver

from dragon.adapters import get_adapter
from dragon.core.metrics import dual_axis_score, over_block_rate, under_block_rate

_DATASET_DIR = Path(__file__).parent / "dataset"


def load_dataset() -> list[Sample]:
    field_spec = FieldSpec(
        input="input",
        target="expected_verdict",
        id="id",
        metadata=["category", "difficulty", "lang", "provenance"],
    )
    attacks = json_dataset(str(_DATASET_DIR / "attacks.jsonl"), field_spec)
    benign = json_dataset(str(_DATASET_DIR / "benign.jsonl"), field_spec)
    return list(attacks) + list(benign)


@solver
def _guardrail_solver(adapter_name: str) -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        adapter = get_adapter(adapter_name)
        verdict = await adapter.check(state.input_text, None)
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
def ideological_censorship(adapter: str = "null") -> Task:
    """Benchmark ideological over-block bias on the dual axis (under-block × over-block).

    This is a model-family module: the subject under test is a raw model or guardrail
    that may refuse legitimate political, historical, and social questions due to
    ideological bias (over-block), while the benchmark also requires it to block
    genuinely harmful political content such as incitement, doxxing, and attack planning.

    High over_block_rate here signals ideological censorship of legitimate discourse.

    Args:
        adapter: Name of the guardrail adapter to evaluate (default: 'null' baseline).
    """
    return Task(
        dataset=load_dataset(),
        solver=_guardrail_solver(adapter),
        scorer=verdict_scorer(),
    )
