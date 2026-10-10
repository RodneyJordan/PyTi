# pad

Small control plane for jobs made of steps.

Each step can `plan` (read-only), `apply` (do the work), and `undo` (compensate).
Drivers (fake, later SSH / Ansible / DNS) sit behind the context. The engine
does not know about vRO, Jenkins, or VirtualBox.

## Dev

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
pad run demo --dry-run
pad run demo
```

## Ansible

```bash
python3 -m venv ~/ansible-env
source ~/ansible-env/bin/activate
pip install ansible-core
ansible-playbook ~/hello.yml
cat ~/hello-from-ansible.txt
```

## Status

Phase 1: engine + FakeCompute + pytest. No hypervisors yet.

```mermaid
flowchart TD
    cli["cli.py<br/>pad run job · pad runs"]
    jobs["jobs.py<br/>JOBS name to list of Step"]
    ctx["RunContext<br/>run_id, job, dry_run<br/>outputs, compute, store"]
    exec["engine.execute"]
    plan["step.plan<br/>dry-run, no mutate"]
    apply["step.apply"]
    undo["undo done steps<br/>backwards"]
    fake["FakeCompute"]
    ssh["SshCompute<br/>claim / run / release"]
    mem["FakeStore"]
    sql["SqliteStore<br/>pad.sqlite"]
    runs["pad runs<br/>list_runs"]

    cli --> jobs
    cli --> ctx
    jobs --> exec
    ctx --> exec
    exec -->|dry_run| plan
    exec -->|live| apply
    apply -->|OK| exec
    apply -->|FAILED| undo
    plan --> exec
    ctx --> fake
    ctx --> ssh
    ctx --> mem
    ctx --> sql
    sql --> runs
    mem --> runs
```
