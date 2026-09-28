from __future__ import annotations

from pad.step import Step
from pad.types import RunContext, Status


def execute(steps: list[Step], ctx: RunContext) -> Status:
    done: list[Step] = []
    ctx.store.start(ctx.run_id, ctx.job, ctx.dry_run)
    for step in steps:
        try:
            result = step.plan(ctx) if ctx.dry_run else step.apply(ctx)
            ctx.store.record_step(ctx.run_id, step.name, result.status, result.message)
        except Exception as exc:  # last resort; steps should return FAILED
            result = _failed(f"unhandled error: {exc}")
            _log(ctx, step.name, result)
            if ctx.store is not None:
                ctx.store.record_step(ctx.run_id. step.name, result.status, result.message)
            _compensate(done, ctx)
            if ctx.store is not None:
                ctx.store.finish(ctx.run_id, Status.FAILED)
            return Status.FAILED

        _log(ctx, step.name, result)

        if result.status is Status.FAILED:
            _compensate(done, ctx)
            ctx.store.finish(ctx.run_id, Status.FAILED)
            return Status.FAILED

        ctx.outputs.update(result.outputs)
        if result.status is Status.OK:
            done.append(step)
    ctx.store.finish(ctx.run_id, Status.OK)
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
