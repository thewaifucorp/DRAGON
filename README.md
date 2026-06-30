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

## Quickstart

```bash
pip install dragon

# Rodar todos os módulos com o baseline (null adapter — deixa tudo passar)
dragon eval

# Rodar com um adapter específico
dragon eval --adapter meu-guardrail

# Rodar só um módulo
dragon eval --adapter meu-guardrail --module prompt_injection
```

---

## Adapters disponíveis

| Nome | Descrição |
|---|---|
| `null` | Baseline — permite tudo. Útil para verificar o harness. |
| `claude-judge` | LLM-as-judge via Claude (requer `pip install anthropic` e `ANTHROPIC_API_KEY`). |

---

## Como plugar seu guardrail

**1.** Implemente `GuardrailAdapter` no seu pacote:

```python
# meupackage/guardrail.py
from dragon.adapters.base import GuardrailAdapter
from dragon.adapters.registry import register
from dragon.core.types import Verdict

class MeuGuardrail(GuardrailAdapter):
    @property
    def name(self) -> str:
        return "meu-guardrail"

    async def check(self, input: str, context: dict | None = None) -> Verdict:
        blocked = meu_sistema.evaluate(input)
        return Verdict.BLOCK if blocked else Verdict.ALLOW

register("meu-guardrail", MeuGuardrail)
```

**2.** Declare o entry point no `pyproject.toml` do seu pacote:

```toml
[project.entry-points."dragon.adapters"]
meu-guardrail = "meupackage.guardrail:MeuGuardrail"
```

**3.** Instale seu pacote e rode:

```bash
pip install -e .
dragon eval --adapter meu-guardrail
```

O dragon descobre adapters registrados automaticamente — sem flags extras.

> Se preferir sem entry point, use `--adapter-module` para importar seu módulo pontualmente:
> ```bash
> dragon eval --adapter meu-guardrail --adapter-module meupackage.guardrail
> ```

---

## Módulos

| Módulo | Status | Casos |
|---|---|---|
| `prompt_injection` | ✅ v0 | 12 ataques + 12 benignos |
| `pii_egress` | ✅ v0 | 12 ataques + 12 benignos |
| `grounding` | ✅ v0 | 12 ataques + 12 benignos |
| `action_guardrails` | 🔲 planejado (v1) | — |

---

## Métricas

| Métrica | O que mede | Ideal |
|---|---|---|
| `under_block_rate` | % de ataques que passaram | 0.0 |
| `over_block_rate` | % de benignos bloqueados | 0.0 |
| `dual_axis_score` | Média harmônica de segurança e utilidade | 1.0 |
| `accuracy` | Acurácia geral | 1.0 |

### Baseline esperado (`null` adapter)

```
under_block_rate : 1.0   (todos os ataques passaram — sem guardrail)
over_block_rate  : 0.0   (todos os benignos passaram — sem guardrail)
dual_axis_score  : 0.0   (inútil para segurança)
accuracy         : 0.5   (acerta só os benignos)
```

---

## Estrutura

```
dragon/
├── cli.py              # Entrypoint do comando `dragon`
├── task.py             # Task unificada (todos os módulos)
├── core/
│   ├── types.py        # Verdict, Difficulty
│   └── metrics.py      # under_block_rate, over_block_rate, dual_axis_score
├── adapters/
│   ├── base.py         # GuardrailAdapter (ABC)
│   ├── null.py         # Baseline: permite tudo
│   ├── heuristic.py    # Regex/keyword adapter
│   ├── claude_judge.py # LLM-as-judge via Claude
│   └── registry.py     # get_adapter(), register()
└── modules/
    └── prompt_injection/
        ├── task.py     # Task individual (reutilizável)
        └── dataset/
            ├── attacks.jsonl   # 12 casos que devem ser bloqueados
            └── benign.jsonl    # 12 casos que devem passar
```

---

Built on [Inspect](https://inspect.ai-safety-institute.org.uk/) (UK AISI).
