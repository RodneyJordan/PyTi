from __future__ import annotations

from pad.step import Step
from pad.steps import ClaimWorker, ReleaseWorker, RunCommand

JOBS: dict[str, list[Step]] = {
    "demo": [
        ClaimWorker(),
        RunCommand(argv=["bazel", "test", "//app:test"]),
        RunCommand(argv=["jenkins", "test1", "//app:test"]),
        ReleaseWorker(),
    ]
}


def get_job(name: str) -> list[Step]:
    try:
        return list(JOBS[name])
    except KeyError as exc:
        known = ", ".join(sorted(JOBS))
        raise SystemExit(f"unknown job {name!r}; known: {known}") from exc
