
from datetime import datetime
from random import randrange
from time import sleep
from typing import Callable


def safety_wait() -> None:
    """
    Waits until a randomly selected number of minutes.
    The number of minutes to wait is guaranteed to be greater at night.
    """

    def wait_random_range(start: int, end: int) -> None:
        random = randrange(start, end)
        sleep(random)

    night = datetime.now().hour < 8
    if night:
        one_hour = 60 * 60
        wait_random_range(one_hour * 2, one_hour * 4)
    else:
        fifteen_minutes = 60 * 15
        wait_random_range(fifteen_minutes, fifteen_minutes * 3)


def until_successive_failures(func: Callable[[None], None], max_fails: int):
    """
    Runs a given function until it
    fails a given number of times in a row.

    func -- the function to run
    max_fails -- the amount of times to try the function
    """
    failures = 0
    while True:
        try:
            func()
        except Exception as exp:
            failures += 1
            if failures >= max_fails:
                raise exp
        else:
            failures = 0
