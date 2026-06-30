import argparse
import sys


def _cmd_eval(args: argparse.Namespace) -> None:
    import importlib

    from inspect_ai import eval as inspect_eval
    from dragon.task import dragon

    for mod in args.adapter_module:
        importlib.import_module(mod)

    inspect_eval(dragon(adapter=args.adapter, module=args.module))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dragon",
        description="DRAGON — Diagnostic Robustness of AI Guardrails On NLP",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    eval_cmd = sub.add_parser("eval", help="Run the benchmark against a guardrail adapter.")
    eval_cmd.add_argument(
        "--adapter",
        default="null",
        metavar="NAME",
        help="Guardrail adapter to evaluate (default: null). E.g. heuristic, claude-judge.",
    )
    eval_cmd.add_argument(
        "--module",
        default=None,
        metavar="NAME",
        help="Run only this module. Omit to run all modules. E.g. prompt_injection.",
    )
    eval_cmd.add_argument(
        "--adapter-module",
        default=[],
        metavar="DOTTED.PATH",
        action="append",
        help="Python module to import before running (registers external adapters). Repeatable.",
    )

    args = parser.parse_args()

    if args.command == "eval":
        _cmd_eval(args)
    else:
        parser.print_help()
        sys.exit(1)
