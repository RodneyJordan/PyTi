from __future__ import annotations

from pad.step import Step
from pad.steps import ClaimWorker, ReleaseWorker, RunCommand, RunPlaybook

JOBS: dict[str, list[Step]] = {
    "demo": [
        ClaimWorker(),
        RunCommand(argv=["cat", "hello.txt"]),
        ReleaseWorker(),
    ],

    "demo-ssh": [
        ClaimWorker(),
        RunCommand(argv=["./hello_world.sh"]),
        RunCommand(argv=["cat", "hello-from-pad.txt"]),
        ReleaseWorker(),
    ],

    "demo-ansible": [
        ClaimWorker(),
        RunPlaybook(argv=["ansible-playbook", "hello.yml"]),
        RunCommand(argv=["cat", "hello-from-ansible.txt"]),
        ReleaseWorker(),
    ]
}


def get_job(name: str) -> list[Step]:
    try:
        return list(JOBS[name])
    except KeyError as exc:
        known = ", ".join(sorted(JOBS))
        raise SystemExit(f"unknown job {name!r}; known: {known}") from exc
