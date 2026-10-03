import sqlite3

class SqliteStore:

    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                job TEXT NOT NULL,
                dry_run INTEGER NOT NULL,
                status TEXT NOT NULL,
                finished INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                seq INTEGER NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );
        """)

    def start(self, run_id: str, job: str, dry_run: bool) -> None:
        self.conn.execute(
            """
            INSERT INTO runs (run_id, job, dry_run, status, finished)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, job, int(dry_run), "", 0),
        )
        self.conn.commit()

    def record_step(self, run_id: str, name: str, status: Status, message: str) -> None:
        seq = self.conn.execute(
            "SELECT COUNT(*) FROM steps WHERE run_id = ?",
            (run_id,),
        ).fetchone()[0]
        self.conn.execute(
            """
            INSERT INTO steps (run_id, name, status, message, seq)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, name, status.value, message, seq),
        )
        self.conn.commit()

    def finish(self, run_id: str, status: Status) -> None:
        self.conn.execute(
            """
            UPDATE runs
            SET status = ?, finished = 1
            WHERE run_id = ?
            """,
            (status.value, run_id),
        )
        self.conn.commit()

    def list_runs(self) -> list[dict]:
        runs = list()
        rows = self.conn.execute(
            "SELECT run_id, job, dry_run, status, finished FROM runs",
        )
        for row in rows:
            run = {
                "run_id": row[0], 
                "job": row[1], 
                "dry_run": bool(row[2]), 
                "status": row[3], 
                "finished": bool(row[4]),
                "steps": []
                }
            steps = self.conn.execute(
                "SELECT name, status, message FROM steps WHERE run_id = ? ORDER BY seq", [row[0]]
            ) 
            
            for step in steps:
                run["steps"].append({
                    "name": step[0],
                    "status": step[1],
                    "message": step[2]
                })

            runs.append(run)
        return runs