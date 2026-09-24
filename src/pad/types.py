from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class Status(str, Enum):
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    status: Status
    message: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)


class Logger(Protocol):
    def info(self, step: str, result: StepResult) -> None: ...


class ComputeDriver(Protocol):
    def claim(self, worker_id: str | None) -> dict[str, Any]: ...

    def run(self, worker_id: str, command: list[str]) -> dict[str, Any]: ...

    def release(self, worker_id: str, dirty: bool = False) -> None: ...


class RunStore(Protocol):
    def start(self, run_id: str, job: str, dry_run: bool) -> None: ...

    def record_step(self, run_id: str, name: str, status: Status, message: str) -> None: ...

    def finish(self, run_id: str, status: Status) -> None: ...

    def list_runs(self) -> list[dict]: ...

@dataclass
class RunContext:
    run_id: str
    job: str
    dry_run: bool
    vars: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    compute: ComputeDriver | None = None
    store: RunStore | None = None
    log: Logger | None = None

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.outputs:
            return self.outputs[key]
        return self.vars.get(key, default)
