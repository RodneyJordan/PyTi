from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FakeCompute:
    """In-memory compute backend for tests and dry development."""

    fail_run: bool = False
    fail_claim: bool = False
    fail_name: str = ""
    next_id: int = 1
    claimed: dict[str, bool] = field(default_factory=dict)
    ran: list[tuple[str, list[str]]] = field(default_factory=list)
    released: list[tuple[str, bool]] = field(default_factory=list)

    def claim(self, worker_id: str | None) -> dict[str, object]:
        wid = worker_id or f"fake-{self.next_id}"
        self.next_id += 1
        if self.fail_claim:
            self.claimed[wid] = False
            return {"exit_code": 1, "stderr": "claim failure", "id": wid}
        self.claimed[wid] = True
        return {"exit_code": 0, "stderr": "claimed", "id": wid}

    def run(self, worker_id: str, command: list[str]) -> dict[str, object]:
        self.ran.append((worker_id, command))
        if self.fail_name == command[0]:
            return {"exit_code": 1, "stderr": "injected failure"}
        elif self.fail_run:
            return {"exit_code": 1, "stderr": "injected failure"}
        return {"exit_code": 0, "stderr": ""}

    def release(self, worker_id: str, dirty: bool = False) -> None:
        self.claimed[worker_id] = False
        self.released.append((worker_id, dirty))

@dataclass
class FakeStore:
    """In-memory storage for testing and development"""

    id: str = ""
    job_name: str = ""
    started: bool = False
    finished: bool = False
    steps: dict[tuple[str, dict[Status, str]]] = field(default_factory=dict)
    status: str = ""

    def start(self, run_id: str, job: str, dry_run: bool) -> None:
        # I don't really care about that dry_run bool at this time
        self.id = run_id
        self.job_name = job
        self.start = True
        return

    def record_step(self, run_id: str, name: str, status: Status, message: str) -> None:
        self.status = status.value
        self.step[name].append(status, message)
        return

    def finish(self, run_id: str, status: Status) -> None:
        self.finished = True

    def list_runs(self) -> list[dict]:
        runs: list[dict] = []
        for step in self.steps:
            runs.append(self.steps[step])

        return runs

        