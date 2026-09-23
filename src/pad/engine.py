from __future__ import annotations

from pad.step import Step
from pad.types import RunContext, Status


def execute(steps: list[Step], ctx: RunContext) -> Status:
    done: list[Step] = []
    for step in steps:
        try:
            result = step.plan(ctx) if ctx.dry_run else step.apply(ctx)
        except Exception as exc:  # last resort; steps should return FAILED
            result = _failed(f"unhandled error: {exc}")
            _log(ctx, step.name, result)
            _compensate(done, ctx)
            return Status.FAILED

        _log(ctx, step.name, result)

        if result.status is Status.FAILED:
            _compensate(done, ctx)
            return Status.FAILED

        ctx.outputs.update(result.outputs)
        if result.status is Status.OK:
            done.append(step)

    return Status.OK


def _compensate(done: list[Step], ctx: RunContext) -> None:
    for prior in reversed(done):
        try:
            undo_result = prior.undo(ctx)
        except Exception as exc:
            undo_result = _failed(f"undo crashed: {exc}")
        _log(ctx, f"{prior.name}.undo", undo_result)


def _log(ctx: RunContext, name: str, result) -> None:
    if ctx.log is not None:
        ctx.log.info(name, result)


def _failed(message: str):
    from pad.types import StepResult

    return StepResult(Status.FAILED, message)
