# coding=utf-8
from threading import Thread, Event
# from BLL.app import Parameter as pa
import time 

class Timer(Thread):
    """
    # Call a _function after a specified number of seconds:
    t = timer.Timer("repeat_th", False, 5.0, quick_test, "repeat", args=[], kwargs={})
    t.start()
    # reset the timer
    t.reset()
    # stop the timer"s action if it"s still waiting
    t.cancel()
    """

    def __init__(self, function, name, args=(), kwargs={}, daemon=True, type="before", interval=0, forever=False):
        Thread.__init__(self, name=name, daemon=daemon)
        self._interval = interval
        self._function = function
        self._type = type
        self._args = args
        self._kwargs = kwargs
        self._finished = Event()
        self._resetted = True
        self._canceled = False
        self._forever = forever

    def cancel(self):
        self._canceled = True
        self._finished.set()

    def run(self):
        # if not self._forever:
        #     pa.TIMER_RUNNING.append(self)
        if self._type == "before":
            self._run_before()
        elif self._type == "after":
            self._run_after()
        elif self._type == "repeat":
            self._run_repeat()


    def reset(self, interval=None):
        if interval:
            self._interval = interval
        self._resetted = True
        self._finished.set()
        self._finished.clear()

    def _run_before(self):
        if not self._finished.isSet():
            self._function(*self._args, **self._kwargs)
        while self._resetted:
            self._resetted = False
            self._finished.wait(self._interval)

    def _run_after(self):
        while self._resetted:
            self._resetted = False
            self._finished.wait(self._interval)
        if not self._finished.isSet():
            self._function(*self._args, **self._kwargs)

    def _run_repeat(self):
        while not self._finished.isSet():
            self._finished.wait(self._interval)
            if self._canceled == False:
                self._function(*self._args, **self._kwargs)
