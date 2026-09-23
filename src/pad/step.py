from __future__ import annotations

from typing import Protocol

from pad.types import RunContext, StepResult


class Step(Protocol):
    name: str

    def plan(self, ctx: RunContext) -> StepResult: ...

    def apply(self, ctx: RunContext) -> StepResult: ...

    def undo(self, ctx: RunContext) -> StepResult: ...
