from enum import Enum
from threading import Thread, Condition
from time import sleep
import logging

logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s',)

WAIT_TIME_GREEN_TO_YELLOW = 5
WAIT_TIME_YELLOW_TO_RED = 1


class Color(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class Semaphore:

    def __init__(self, color: Color = None):
        self.current_light = color

    def change(self, color: Color = None):
        prev_color = self.current_light

        if color is not None:
            self.current_light = color
        else:
            if self.current_light == Color.RED:
                self.current_light = Color.GREEN
            elif self.current_light == Color.YELLOW:
                sleep(WAIT_TIME_YELLOW_TO_RED)
                self.current_light = Color.RED
            elif self.current_light == Color.GREEN:
                sleep(WAIT_TIME_GREEN_TO_YELLOW)
                self.current_light = Color.YELLOW
            else:
                self.current_light = Color.RED
        logging.debug("From > %s, To > %s" % (prev_color, self.current_light))


semaphore1 = Semaphore(color=Color.RED)
semaphore2 = Semaphore(color=Color.RED)
semaphore3 = Semaphore(color=Color.RED)
semaphore4 = Semaphore(color=Color.RED)


def semaphore_handle(condition: Condition, semaphore: Semaphore):
    while True:
        with condition:
            semaphore.change()
            condition.notify()


def main():
    condition = Condition()

    thread1 = Thread(name="semaphore1", target=semaphore_handle, args=(condition, semaphore1))
    thread2 = Thread(name="semaphore2", target=semaphore_handle, args=(condition, semaphore2))
    thread3 = Thread(name="semaphore3", target=semaphore_handle, args=(condition, semaphore3))
    thread4 = Thread(name="semaphore4", target=semaphore_handle, args=(condition, semaphore4))

    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()


if __name__ == '__main__':
    main()

