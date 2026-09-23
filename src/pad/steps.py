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
        result = ctx.compute.run(ctx.get("worker_id"), self.argv)
        if result.get("exit_code") != 0:
            return StepResult(Status.FAILED, result.get("stderr", "nonzero exit"))
        return StepResult(Status.OK, "command finished", {"exit_code": 0})

    def undo(self, ctx: RunContext) -> StepResult:
        return StepResult(Status.SKIPPED, "command has no undo")


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
