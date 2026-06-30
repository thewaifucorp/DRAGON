# DRAGON

**D**iagnostic **R**obustness of **A**I **G**uardrails **O**n **N**LP

Benchmark composable que mede se um sistema de guardrail (ou modelo cru) é **seguro sem ser inútil**.

---

## O ângulo

A maioria dos benchmarks mede só um eixo: o sistema bloqueou o perigoso? DRAGON mede os dois erros:

| Erro | Nome | Consequência |
|---|---|---|
| Deixou passar o perigoso | **under-block** | Falha de segurança |
| Recusou o legítimo | **over-block** | "Nanny tax" — falha de utilidade |

**Pontuar alto = ser seguro E útil.** Um guardrail que bloqueia tudo tira nota péssima.

---

## Módulos (v0)

| Módulo | Status |
|---|---|
| `prompt-injection` | ✅ v0 |
| `pii-egress` | 🔲 planejado |
| `grounding` | 🔲 planejado |
| `action-guardrails` | 🔲 planejado (v1) |

---

## Quickstart

```bash
pip install -e ".[dev]"

# Rodar com o baseline (null adapter — deixa tudo passar)
inspect eval dragon/modules/prompt_injection/task.py --task prompt_injection

# Rodar com um adapter específico
inspect eval dragon/modules/prompt_injection/task.py --task prompt_injection --task-arg adapter=meu-guardrail
```

---

## Como plugar um guardrail

Implemente `GuardrailAdapter` e registre:

```python
from dragon.adapters.base import GuardrailAdapter
from dragon.adapters.registry import register
from dragon.core.types import Verdict

class MeuGuardrail(GuardrailAdapter):
    @property
    def name(self) -> str:
        return "meu-guardrail-v1"

    async def check(self, input: str, context: dict | None = None) -> Verdict:
        # chame seu sistema aqui
        blocked = meu_sistema.evaluate(input)
        return Verdict.BLOCK if blocked else Verdict.ALLOW

register("meu-guardrail", MeuGuardrail)
```

---

## Métricas

| Métrica | O que mede | Ideal |
|---|---|---|
| `under_block_rate` | % de ataques que passaram | 0.0 |
| `over_block_rate` | % de benignos bloqueados | 0.0 |
| `dual_axis_score` | Média harmônica de segurança e utilidade | 1.0 |
| `accuracy` | Acurácia geral (via Inspect) | 1.0 |

---

## Estrutura

```
dragon/
├── core/
│   ├── types.py          # Verdict, Difficulty
│   └── metrics.py        # under_block_rate, over_block_rate, dual_axis_score
├── adapters/
│   ├── base.py           # GuardrailAdapter (ABC)
│   ├── null.py           # Baseline: permite tudo
│   └── registry.py       # get_adapter(), register()
└── modules/
    └── prompt_injection/
        ├── task.py        # Inspect Task
        └── dataset/
            ├── attacks.jsonl   # 12 casos que devem ser bloqueados
            └── benign.jsonl    # 12 casos que devem passar
```

---

## Baseline esperado (null adapter)

```
under_block_rate : 1.0   (todos os ataques passaram — sem guardrail)
over_block_rate  : 0.0   (todos os benignos passaram — sem guardrail)
dual_axis_score  : 0.0   (inútil para segurança)
accuracy         : 0.5   (acerta só os benignos)
```

---

Built on [Inspect](https://inspect.ai-safety-institute.org.uk/) (UK AISI).
