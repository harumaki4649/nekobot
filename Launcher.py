import shardedBot2
from multiprocessing import Process, Pipe, Queue
import asyncio
import shutil
import os
from signal import SIGKILL

shards = 128
shards_per_instance = 16
instances = int(shards / shards_per_instance)
processes = list()

def wait(delay: int):
    loop.run_until_complete(asyncio.sleep(delay))

processes_owo = {}

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    executable = str(shutil.which("python3.6") or shutil.which("py")).split("/")[-1]
    queue = list()
    for i in range(0, instances):
        start = i * shards_per_instance
        last = min(start + shards_per_instance, shards)
        ids = list(range(start, last))
        processes_owo[str(i)] = {
            "ids": ids,
            "process": None
        }

    ipc_queue = Queue()

    for powo in processes_owo:
        listen, send = Pipe()
        p = Process(target=shardedBot2.NekoBot, args=(int(powo), instances, shards, processes_owo[powo]["ids"], send, ipc_queue))
        p.start()
        processes_owo[powo]["process"] = p
        print("Launching Instance {} (PID {})".format(powo, p.pid))
        processes.append(p.pid)

        if listen.recv() == 1:
            print("Instance {} Launched".format(powo))
        listen.close()

    try:
        while True:
            try:
                for powo in processes_owo:
                    proc = processes_owo[powo].get("process")
                    if not proc.is_alive():
                        listen, send = Pipe()
                        p = Process(target=shardedBot2.NekoBot, args=(int(powo), instances, shards, processes_owo[powo]["ids"], send, ipc_queue))
                        p.start()
                        processes_owo[powo]["process"] = p
                        print("Relaunched {}".format(powo))
                        processes.append(p.pid)

                        if listen.recv() == 1:
                            print("Instance {} Launched".format(p))
                        listen.close()
            except Exception as e:
                print("Failed to restart process, {}".format(e))
            wait(5)
    except KeyboardInterrupt:
        for process in processes:
            os.kill(process, SIGKILL)
            print("Killed {}".format(process))
        print("Finished")
