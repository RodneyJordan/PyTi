from __future__ import annotations

from dataclasses import dataclass, field

from pad.types import RunContext, Status, StepResult


@dataclass
class ClaimWorker:
    name: str = "claim_worker"

    def plan(self, ctx: RunContext) -> StepResult:
        if ctx.get("worker_id"):
            return StepResult(Status.SKIPPED, "worker already claimed")
        return StepResult(
            Status.OK,
            "would claim a worker",
            {"worker_id": "dry-worker"},
        )

    def apply(self, ctx: RunContext) -> StepResult:
        if ctx.dry_run:
            return self.plan(ctx)
        if ctx.compute is None:
            return StepResult(Status.FAILED, "no compute driver")
        info = ctx.compute.claim(ctx.get("worker_id"))
        if info.get("exit_code") != 0:
            return StepResult(Status.FAILED, info.get("stderr", "failed to claim worker"))
        return StepResult(Status.OK, "claimed", {"worker_id": info["id"]})

    def undo(self, ctx: RunContext) -> StepResult:
        wid = ctx.get("worker_id")
        if not wid:
            return StepResult(Status.SKIPPED, "nothing to release")
        if ctx.compute is None:
            return StepResult(Status.SKIPPED, "no compute driver")
        ctx.compute.release(wid, dirty=True)
        return StepResult(Status.OK, f"released {wid}")


@dataclass
class RunCommand:
    name: str = "run_command"
    argv: list[str] = field(default_factory=list)

    def plan(self, ctx: RunContext) -> StepResult:
        if not ctx.get("worker_id"):
            return StepResult(Status.FAILED, "no worker_id")
        return StepResult(Status.OK, f"would run {self.argv}")

    def apply(self, ctx: RunContext) -> StepResult:
        if ctx.dry_run:
            return self.plan(ctx)
        if ctx.compute is None:
            return StepResult(Status.FAILED, "no compute driver")
        filled = self._fill(self.argv, ctx)
        if isintance(filled, StepResult):
            return filled
        result = ctx.compute.run(ctx.get("worker_id"), filled)
        if result.get("exit_code") != 0:
            return StepResult(Status.FAILED, result.get("stderr", "nonzero exit"))
        text = str(result.get("stdout") or "").strip()
        return StepResult(Status.OK, text or "ok")

    def undo(self, ctx: RunContext) -> StepResult:
        return StepResult(Status.SKIPPED, "command has no undo")

    def _fill(self, argv: list[str], ctx: RunContext) -> list[str] | StepResult:
        out = []
        for arg in argv:
            if arg.startswith("{") and arg.endswith("}") and len(arg) > 2:
                key = arg[1:-1]
                val = ctx.get(key)
                if val is None:
                    return StepResult(Status.FAILED, f"missing output : {key}")
                out.append(str(val))
            else:
                out.append(arg)
        return out

@dataclass
class RunPlaybook:
    name: str = "run_playbook"
    argv: list[str] = field(default_factory=list)

    def plan(self, ctx: RunContext) -> StepResult:
        if not ctx.get("worker_id"):
            return StepResult(Status.SKIPPED, "no worker_id")
        return StepResult(Status.OK, "would call a playbook")

    def apply(self, ctx: RunContext) -> StepResult:
        if ctx.dry_run:
            return self.plan(ctx)
        wid = ctx.get("worker_id")
        if not wid:
            return StepResult(Status.SKIPPED, "no worker_id")
        if ctx.compute is None:
            return StepResult(Status.FAILED)
        result = ctx.compute.run(ctx.get("worker_id"), self.argv)
        if result.get("exit_code") != 0:
            return StepResult(Status.FAILED, result.get("stderr", "Ansible failure..."))
        text = str(result.get("stdout") or "").strip()
        return StepResult(Status.OK, text or "ok")

@dataclass
class RunJenkinsJob:

    job: str
    name: str = "run_jenkins"

    def plan(self, ctx: RunContext) -> StepResult:
        if not ctx.get("worker_id"):
            return StepResult(Status.SKIPPED, "no worker_id")
        return StepResult(Status.OK, "would run a jenkins job")

    def apply(self, ctx: RunContext) -> StepResult:
        import json
        import time

        base = f"http://localhost:8080/job/{self.job}"
        auth = ["--user", f"rodney:11816bead6670f73f3f8cd0a6f15320e71"]

        if ctx.dry_run:
            return self.plan(ctx)
        wid = ctx.get("worker_id")
        if not wid:
            return StepResult(Status.SKIPPED, "no worker_id")
        if ctx.compute is None:
            return StepResult(Status.FAILED)
        
        # Get last build
        info = ctx.compute.run(wid, ["curl", "-fsS", f"{base}/api/json", *auth])
        if info.get("exit_code") != 0:
            return StepResult(Status.FAILED, info.get("stderr") or "failed to read job")
        number = json.loads(info["stdout"])["nextBuildNumber"]

        # Trigger build
        info = ctx.compute.run(wid, ["curl", "-fsS", "-X", "POST", f"{base}/build", *auth])
        if info.get("exit_code") != 0:
            return StepResult(Status.FAILED, info.get("stderr") or "failed to launch job")
        
        # Poll
        for _ in range(30):
            info = ctx.compute.run(wid, ["curl", "-fsS", f"{base}/{number}/api/json", *auth])
            if info.get("exit_code") == 0:
                data = json.loads(info.get("stdout") or "{}")
                result = data.get("result")
                if result == "SUCCESS":
                    return StepResult(Status.OK, f"build {number} SUCCESS")
                if result:
                    return StepResult(Status.FAILED, f"build {number} {result}")
            time.sleep(2)
        return StepResult(Status.FAILED, f"build {number} timed out")

@dataclass
class RunGit:
    name: str = "run_git"
    repo: str = "http://192.168.86.142:3000/"
    dest: str
    ref: str = "master"

    def plan(self, ctx: RunContext) -> StepResult:
        if not ctx.get("worker_id"):
            return StepResult(Status.SKIPPED, "no worker_id")
        return StepResult(Status.OK, "would run a git command...")

    def apply(self, ctx: RunContext) -> StepResult:
        dest = self.dest or self.repo.rstrip("/").split("/")[-1].removesuffix(".git")
        argv = ["git", "clone", "--depth", "1"]
        if self.ref:
            argv += ["--branch", self.ref]
        argv += [self.repo, dest]
        info = ctx.compute.run(ctx.get("worker_id"), argv)
        if info.get("exit_code", 1) != 0:
            return StepResult(Status.FAILED, str(info.get("stdout)") or "git clone failed.."))
        return StepResult(Status.OK, f"cloned {dest}", {"git_dest": dest})

    def undo(self, ctx: RunContext) -> StepResult:
        return StepResult(Status.SKIPPED, "nothing to undo")

@dataclass
class ReleaseWorker:
    name: str = "release_worker"

    def plan(self, ctx: RunContext) -> StepResult:
        if not ctx.get("worker_id"):
            return StepResult(Status.SKIPPED, "no worker_id")
        return StepResult(Status.OK, "would release worker")

    def apply(self, ctx: RunContext) -> StepResult:
        if ctx.dry_run:
            return self.plan(ctx)
        wid = ctx.get("worker_id")
        if not wid:
            return StepResult(Status.SKIPPED, "no worker_id")
        if ctx.compute is None:
            return StepResult(Status.FAILED, "no compute driver")
        ctx.compute.release(wid, dirty=False)
        return StepResult(Status.OK, f"released {wid}")

    def undo(self, ctx: RunContext) -> StepResult:
        return StepResult(Status.SKIPPED, "already released or never claimed")
