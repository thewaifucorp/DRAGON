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
def cross_lingual_bypass(adapter: str = "null") -> Task:
    """Benchmark cross-lingual jailbreak bypass resistance on the dual axis.

    This is a model-family module: tests whether guardrails trained primarily on
    English correctly handle attacks delivered in Portuguese, Spanish, French,
    German, Arabic, encoded text, pig latin, or language-switching prompts.

    Benign cases cover legitimate multilingual content (PT-BR questions, code with
    non-English comments, translation requests) that should not be over-blocked.

    Args:
        adapter: Name of the guardrail adapter to evaluate (default: 'null' baseline).
    """
    return Task(
        dataset=load_dataset(),
        solver=_guardrail_solver(adapter),
        scorer=verdict_scorer(),
    )
