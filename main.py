from enum import Enum
from threading import Thread, Condition
from time import sleep
import pygame
from pygame.sprite import Sprite, Group


class Color(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class Direction(Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


class Context:
    def __init__(self, current_directions: [Direction], velocity: int = 5):
        self.current_directions = current_directions
        self.velocity = velocity

    def __str__(self) -> str:
        return str(self.current_directions)


class Semaphore(Thread, Sprite):

    def __init__(self, name: str, direction: Direction, condition: Condition, position: tuple = (0, 0),
                 context: Context = None, color: Color = None):
        self.direction = direction
        self.current_light = color
        self.set_light(color)
        self.rect = self.image.get_rect(center=position)
        self.condition = condition
        self.context = context

        Thread.__init__(self, name=name, args=(self.condition, ))
        Sprite.__init__(self)
        self.name = name

    def change(self, color: Color = None):
        self.set_light(color)

    def set_light(self, color: Color):
        self.current_light = color
        src = r"resources/%s-%s.png" % (str(self.direction.value).lower(), str(color.value).lower())
        self.image = pygame.image.load(src).convert_alpha()

    def __str__(self) -> str:
        return "%s: %s" % (self.name, str(self.current_light))

    def run(self):
        with self.condition:
            while True:
                self.condition.acquire()
                self.change(Color.GREEN)
                sleep(5)
                self.change(Color.YELLOW)
                sleep(1)
                self.change(Color.RED)
                self.condition.wait()

    def stop(self):
        self.join()


class Manager(Thread):
    def __init__(self, condition: Condition = Condition(), context: Context = None):
        self.condition = condition
        self.is_running = True
        self.context = context
        super().__init__(name="manager", args=(self.condition, ))

    def run(self):
        with self.condition:
            while self.is_running:
                self.condition.acquire()
                self.condition.notify()
                self.condition.wait(self.context.velocity)

    def stop(self):
        self.is_running = False
        self.join()


def main():
    # Init
    pygame.init()
    screen = pygame.display.set_mode((825, 599))

    # Headless process
    condition = Condition()
    context = Context(current_directions=[Direction.NORTH, Direction.SOUTH])

    manager = Manager(condition=condition, context=context)

    semaphore1 = Semaphore(name="semaphore1", condition=condition, context=context, position=(452, 252),
                           direction=Direction.NORTH, color=Color.RED)
    semaphore2 = Semaphore(name="semaphore2", condition=condition, context=context, position=(415, 388),
                           direction=Direction.SOUTH, color=Color.RED)
    semaphore3 = Semaphore(name="semaphore3", condition=condition, context=context, position=(565, 330),
                           direction=Direction.EAST, color=Color.RED)
    semaphore4 = Semaphore(name="semaphore4", condition=condition, context=context, position=(330, 328),
                           direction=Direction.WEST, color=Color.RED)

    semaphore1.start()
    semaphore2.start()
    semaphore3.start()
    semaphore4.start()

    manager.start()

    # Animations
    image = pygame.image.load(r'resources/map.png')
    group = Group(semaphore1, semaphore2, semaphore3, semaphore4)

    running = True

    while running:
        screen.blit(image, (0, 0))
        group.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    main()

