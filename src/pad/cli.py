from __future__ import annotations

import argparse
import uuid

from pad.drivers.fake import FakeCompute
from pad.engine import execute
from pad.jobs import get_job
from pad.types import RunContext, Status, StepResult


class PrintLogger:
    def info(self, step: str, result: StepResult) -> None:
        print(f"{step:24} {result.status.value:8} {result.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pad")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="execute a named job")
    run.add_argument("job")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--fail-run", action="store_true", help="fake driver: fail the command")
    run.add_argument("--fail-name", dest="fail_name", default="")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        compute = FakeCompute(fail_run=args.fail_run, fail_name=args.fail_name)
        ctx = RunContext(
            run_id=str(uuid.uuid4())[:8],
            job=args.job,
            dry_run=args.dry_run,
            compute=compute,
            log=PrintLogger(),
        )
        status = execute(get_job(args.job), ctx)
        print(f"result {status.value} run={ctx.run_id}")
        return 0 if status is Status.OK else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
