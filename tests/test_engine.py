from pad.drivers.fake import FakeCompute, FakeStore
from pad.drivers.sqlite_store import SqliteStore
from pad.engine import execute
from pad.jobs import get_job
from pad.types import RunContext, Status


def _ctx(**kwargs) -> RunContext:
    compute = kwargs.pop("compute", FakeCompute())
    store = kwargs.pop("store", FakeStore())
    dry_run = kwargs.pop("dry_run", False)
    return RunContext(
        run_id="t1",
        job="demo",
        dry_run=dry_run,
        compute=compute,
        store=store,
        **kwargs,
    )


def test_happy_path_releases_clean_worker():
    compute = FakeCompute()
    ctx = _ctx(compute=compute)
    assert execute(get_job("demo"), ctx) is Status.OK
    assert ctx.get("worker_id")
    assert compute.claimed[ctx.get("worker_id")] is False
    assert compute.released[-1][1] is False  # not dirty


def test_failed_run_undoes_claim():
    compute = FakeCompute(fail_run=True, fail_claim=False)
    ctx = _ctx(compute=compute)
    assert execute(get_job("demo"), ctx) is Status.FAILED
    wid = ctx.get("worker_id")
    assert wid
    assert compute.claimed[wid] is False
    assert compute.released[-1] == (wid, True)  # dirty release from undo

def test_fail_claim():
    compute = FakeCompute(fail_run=False, fail_claim = True)
    ctx = _ctx(compute=compute)
    assert execute(get_job("demo"), ctx) is Status.FAILED
    assert ctx.get("worker_id") is None
    assert not any(compute.claimed.values())
    assert compute.ran == []

def test_dry_run_does_not_touch_compute():
    compute = FakeCompute()
    ctx = _ctx(compute=compute, dry_run=True)
    assert execute(get_job("demo"), ctx) is Status.OK
    assert ctx.get("worker_id") == "dry-worker"
    assert compute.claimed == {}
    assert compute.ran == []
    assert compute.released == []

def test_store_fail_row():
    store = FakeStore()
    ctx = _ctx(store=store)
    store.start(ctx.run_id, "demo", False)
    store.record_step(ctx.run_id, "claim_worker", Status.FAILED, "claim failure")
    store.finish(ctx.run_id, Status.FAILED)
    run = store.list_runs()[0]
    assert run["run_id"] == ctx.run_id
    assert run["job"] == "demo"
    assert run["status"] == "failed"
    assert run["finished"] is True
    assert run["steps"][0]["name"] == "claim_worker"
    assert run["steps"][0]["status"] == "failed"

def test_sqlite_start(tmp_path):
    path = tmp_path / "pad.sqlite"
    store = SqliteStore(str(path))
    store.start("r1", "demo", False)
    row = store.conn.execute(
        "SELECT run_id, job, dry_run, status, finished FROM runs"
    ).fetchone()
    assert row == ("r1", "demo", 0, "", 0)

def test_sqlite_record_step(tmp_path):
    path = tmp_path / "pad.sqlite"
    store = SqliteStore(str(path))
    store.start("r1", "demo", False)
    store.record_step("r1", "jenkins", Status.OK, "testing")
    store.finish("r1", Status.OK)
    row = store.conn.execute(
        "SELECT run_id, name, status, message, seq FROM steps"
    ).fetchone()
    assert row == ("r1", "jenkins", "ok", "testing", 0)

def test_sqlite_finish(tmp_path):
    path = tmp_path / "pad.sqlite"
    store = SqliteStore(str(path))
    store.start("r1", "demo", False)
    store.record_step("r1", "jenkins", Status.OK, "testing")
    store.finish("r1", Status.OK)
    row = store.conn.execute(
        "SELECT run_id, job, dry_run, status, finished FROM runs WHERE run_id = ?",
        ("r1",),
    ).fetchone()
    assert row == ("r1", "demo", 0, "ok", 1)

def test_sqllite_list_runs(tmp_path):
    path = tmp_path / "pad.sqlite"
    store = SqliteStore(str(path))
    store.start("r1", "demo", False)
    store.record_step("r1", "jenkins", Status.OK, "testing")
    store.finish("r1", Status.OK)
    runs = store.list_runs()
    assert isinstance(runs[0], dict)