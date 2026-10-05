from __future__ import annotations

import argparse
import uuid

from pad.drivers.fake import FakeCompute, FakeStore
from pad.drivers.sqlite_store import SqliteStore
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

    runs = sub.add_parser("runs", help="exectue a list of completed runs")

    args = parser.parse_args(argv)

    if args.cmd == "run":
        if args.ssh:
            compute = SshCompute(hostname=args.ssh, username=args.user)
        else:
            compute = FakeCompute(fail_run=args.fail_run, fail_name=args.fail_name)
        store = SqliteStore("pad.sqlite")
        ctx = RunContext(
            run_id=str(uuid.uuid4())[:8],
            job=args.job,
            dry_run=args.dry_run,
            compute=compute,
            store=store,
            log=PrintLogger(),
        )
        status = execute(get_job(args.job), ctx)
        print(f"result {status.value} run={ctx.run_id}")
        return 0 if status is Status.OK else 1
    elif args.cmd == "runs":
        store = SqliteStore("pad.sqlite")
        for run in store.list_runs():
            last = run["steps"][-1]["name"] if run["steps"] else "-"
            print(f"{run['run_id']} {run['job']} {run['status']} {last}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
