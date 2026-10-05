import shlex
import paramiko

class SshCompute:

    def __init__(self, hostname: str, usernname: str) -> None:
        self.hostname = hostname
        self.username = username
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.worker_id = ""

    def claim(self, worker_id: str | None) -> dict[str, object]:
        self.worker_id = worker_id or self.hostname
         try :
            ssh.connect(
                hostname=self.hostname, 
                username=self.username,
                look_for_keys=True,
                allow_agent=True,
            )
        except Exception as exc:
            return {"exit_code": 1, "stderr": str(exc), "id": self.worker_id}
        return {"exit_code": 0, "stderr": "", "id": self.worker_id}        

    def run(self,worker_id: str, hostname: str, command: list[str]) -> dict[str, object]:
        cmdline = shlex.join(command)
        _stdin, stdout, stderr = self.ssh.exec_command(cmdline)
        exit_code = stdout.channel.recv_exit_status()
        err = stderr.read().decode()
        return {"exit_code": exit_code, "stderr": err}

    def release(self, worker_id: str, dirty: bool = False) -> None:
        self.ssh.close()