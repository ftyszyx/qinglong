import os
import time
import sys
from threading import Thread
import logging


# 输出unity导出工程的日志
class Tail(Thread):
    def __init__(self, filename, tagname, encoding="UTF-8"):
        self._filename = filename
        self._stop_reading = False
        self._tagname = tagname
        self._encoding = encoding
        Thread.__init__(self)

    def run(self):
        print(f"{self._tagname} start read")
        while not os.path.exists(self._filename):
            time.sleep(0.1)
        with open(self._filename, mode="r", encoding=self._encoding) as file:
            while True:
                where = file.tell()
                line = file.readline()
                if self._stop_reading and not line:
                    break
                if not line:
                    time.sleep(1)
                    file.seek(where)
                else:
                    if sys.stdout.closed is True:
                        return
                    # print(f'[{self._tagname}]:{line.rstrip()}')
                    logging.info("[%s]:%s", self._tagname, line.rstrip())
                    sys.stdout.flush()

    def stop(self):
        self._stop_reading = True
        print(f"{self._tagname} stop read")
        # Wait for thread read the remaining log after process quit in 5 seconds
        self.join(5)
