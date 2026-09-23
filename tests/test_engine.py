from pad.drivers.fake import FakeCompute
from pad.engine import execute
from pad.jobs import get_job
from pad.types import RunContext, Status


def _ctx(**kwargs) -> RunContext:
    compute = kwargs.pop("compute", FakeCompute())
    dry_run = kwargs.pop("dry_run", False)
    return RunContext(
        run_id="t1",
        job="demo",
        dry_run=dry_run,
        compute=compute,
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
