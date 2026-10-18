from __future__ import annotations

from pad.step import Step
from pad.steps import ClaimWorker, ReleaseWorker, RunCommand, RunPlaybook, RunJenkinsJob

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
        RunPlaybook(argv=["/home/rodney/ansible-env/bin/ansible-playbook", "hello.yml"]),
        RunCommand(argv=["cat", "hello-from-ansible.txt"]),
        ReleaseWorker(),
    ],

    "demo-jenkins": [
        ClaimWorker(),
        RunJenkinsJob(job="jenkins-demo"),
        RunCommand(argv=["cat", "/opt/jenkins/jenkins-marker.txt"]),
        ReleaseWorker(),
    ],

    "demo-git": [
        ClaimWorker(),
        RunGit(repo="http://192.168.86.142:3000/rodney/server-deployment.git"),
        RunCommand(argv["chmod", "u+x /opt/git/server-deployment/pyti-demo/git_test.sh"]),
        RunCommand(argv["opt/git/server-deployment/pyti-demo/git_test.sh"])
        ReleaseWorker(),

    ]
}


def get_job(name: str) -> list[Step]:
    try:
        return list(JOBS[name])
    except KeyError as exc:
        known = ", ".join(sorted(JOBS))
        raise SystemExit(f"unknown job {name!r}; known: {known}") from exc
