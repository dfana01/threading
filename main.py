from enum import Enum
from threading import Thread, Condition
from time import sleep
import pygame
from pygame.sprite import Sprite, Group
from pygame.rect import Rect
import pygame_textinput

BACKGROUND_COLOR = (51, 60, 87)

FAST_SIMULATION = 10
INTERMEDIATE_SIMULATION = 5
SLOW_SIMULATION = 3


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
    def __init__(self, velocity: int = SLOW_SIMULATION):
        self.velocity = velocity


class Map(Sprite):
    def __init__(self, src: str = r'resources/map.png', position: tuple = (0, 0), context: Context = None):
        Sprite.__init__(self)
        self.image = pygame.image.load(src).convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=position)
        self.rect.topleft = (0, 0)
        self.mask = pygame.mask.from_surface(self.image)
        self.context = context


class Semaphore(Thread, Sprite):

    def __init__(self, name: str, direction: Direction, condition: Condition, position: tuple = (0, 0),
                 context: Context = None, color: Color = None, crosswalk: Rect = None):
        self.direction = direction
        self.current_light = color
        self.set_light(color)
        self.rect = self.image.get_rect(center=position)
        self.condition = condition
        self.context = context
        self.crosswalk = crosswalk

        Thread.__init__(self, name=name, args=(self.condition,))
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
                sleep(self.context.velocity)
                self.change(Color.YELLOW)
                sleep(self.context.velocity * .05)
                self.change(Color.RED)
                self.condition.wait()

    def stop(self):
        self.join()

    def update(self):
        Sprite.update(self)


class Vehicle(Sprite):
    def __init__(self, src: str, start_position: tuple = (0, 0), direction: tuple = (0, 0),
                 context: Context = None, semaphore: Semaphore = None):
        Sprite.__init__(self)
        self.start_position = start_position
        self.position = pygame.math.Vector2(start_position)
        self.dir = pygame.math.Vector2(direction).normalize()
        self.image = pygame.image.load(src).convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=start_position)
        self.context = context
        self.semaphore = semaphore
        self.stop = False

    def update(self):
        if (self.start_position[0] > 528 and self.rect.x < 0) \
                or (self.start_position[0] < 0 and self.rect.x > 528) \
                or (self.start_position[1] < 0 and self.rect.y > 528) \
                or (self.start_position[1] > 528 and self.rect.y < 0):
            self.position = (self.start_position[0], self.start_position[1])

        if self.semaphore.current_light == Color.RED and self.semaphore.crosswalk.colliderect(self.rect):
            return

        self.position += self.dir * self.context.velocity
        self.rect.center = (self.position.x, self.position.y)


class Manager(Thread):
    def __init__(self, condition: Condition = Condition(), context: Context = None):
        self.condition = condition
        self.is_running = True
        self.context = context
        super().__init__(name="manager", args=(self.condition,))

    def run(self):
        with self.condition:
            while self.is_running:
                self.condition.acquire()
                self.condition.notifyAll()
                self.condition.wait(self.context.velocity)

    def stop(self):
        self.is_running = False
        self.join()


class Button:
    def __init__(self, color, text_color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.text_color = text_color

    def draw(self, win, outline=None):
        if outline:
            pygame.draw.rect(win, outline, (self.x - 2, self.y - 2, self.width + 4, self.height + 4), 0)

        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.height), 0)

        if self.text != '':
            font = pygame.font.SysFont('comicsans', 16)
            text = font.render(self.text, 1, self.text_color)
            win.blit(text, (
                self.x + (self.width / 2 - text.get_width() / 2), self.y + (self.height / 2 - text.get_height() / 2)))

    def is_over(self, pos):
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True
        return False


screen = pygame.display.set_mode((640, 480))
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
FONT = pygame.font.Font(None, 16)


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


def main():
    # Init
    pygame.init()
    screen = pygame.display.set_mode((528, 528))
    clock = pygame.time.Clock()
    program_icon = pygame.image.load('resources/icon.png')
    pygame.display.set_icon(program_icon)
    running = True

    # Headless process
    condition = Condition()
    context = Context()

    rect_south = pygame.Rect(190, 145, 145, 40)
    rect_north = pygame.Rect(193, 336, 145, 40)
    rect_west = pygame.Rect(335, 195, 40, 150)
    rect_east = pygame.Rect(145, 195, 40, 150)

    manager = Manager(condition=condition, context=context)

    semaphore_north = Semaphore(name="semaphore1", condition=condition, context=context, position=(345, 330),
                                direction=Direction.NORTH, color=Color.RED, crosswalk=rect_north)
    semaphore_south = Semaphore(name="semaphore2", condition=condition, context=context, position=(193, 169),
                                direction=Direction.SOUTH, color=Color.RED, crosswalk=rect_south)
    semaphore_east = Semaphore(name="semaphore3", condition=condition, context=context, position=(182, 330),
                               direction=Direction.EAST, color=Color.RED, crosswalk=rect_east)
    semaphore_west = Semaphore(name="semaphore4", condition=condition, context=context, position=(345, 172),
                               direction=Direction.WEST, color=Color.RED, crosswalk=rect_west)

    semaphore_north.start()
    semaphore_south.start()
    semaphore_east.start()
    semaphore_west.start()

    manager.start()

    # Animations
    cart_blue_horizontal = Vehicle(src=r'resources/cart-blue-horizontal.png', start_position=(576, 231),
                                   direction=(-1, 0), context=context, semaphore=semaphore_west)
    cart_red_horizontal = Vehicle(src=r'resources/cart-red-horizontal.png', start_position=(-48, 301),
                                  direction=(1, 0), context=context, semaphore=semaphore_east)
    cart_yellow_vertical_1 = Vehicle(src=r'resources/cart-yellow-vertical-1.png', start_position=(229, -32),
                                     direction=(0, 1), context=context, semaphore=semaphore_south)
    cart_yellow_vertical_2 = Vehicle(src=r'resources/cart-yellow-vertical-2.png', start_position=(296, 560),
                                     direction=(0, -1), context=context, semaphore=semaphore_north)

    map = Map(context=context)

    group_general = Group(map)
    group_semaphores = Group(semaphore_north, semaphore_south, semaphore_east, semaphore_west)
    group_vehicles = Group([
        cart_blue_horizontal,
        cart_red_horizontal,
        cart_yellow_vertical_1,
        cart_yellow_vertical_2,
    ])

    input_box = InputBox(420, 365, 75, 18, text=str(INTERMEDIATE_SIMULATION))
    btn_reset = Button((150, 150, 150), (1, 1, 1), 420, 390, 75, 18, "Reset")
    btn_fast = Button((150, 150, 150), (1, 1, 1), 420, 415, 75, 18, "Fast")
    btn_intermediate = Button((150, 150, 150), (1, 1, 1), 420, 440, 75, 18, "Intermediate")
    btn_slow = Button((150, 150, 150), (1, 1, 1), 420, 465, 75, 18, "Slow")

    while running:
        clock.tick(30)

        group_vehicles.update()
        group_semaphores.update()

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                print(event.pos)
                if btn_reset.is_over(event.pos):
                    context.velocity = INTERMEDIATE_SIMULATION
                    input_box.text = INTERMEDIATE_SIMULATION
                if btn_slow.is_over(event.pos):
                    context.velocity = SLOW_SIMULATION
                    input_box.text = SLOW_SIMULATION
                if btn_intermediate.is_over(event.pos):
                    context.velocity = INTERMEDIATE_SIMULATION
                    input_box.text = INTERMEDIATE_SIMULATION
                if btn_fast.is_over(event.pos):
                    context.velocity = FAST_SIMULATION
                    input_box.text = FAST_SIMULATION
            if event.type == pygame.QUIT:
                running = False
            input_box.handle_event(event)
            context.velocity = int(input_box.text)

        screen.fill(BACKGROUND_COLOR)

        group_general.draw(screen)
        group_semaphores.draw(screen)
        group_vehicles.draw(screen)

        btn_reset.draw(screen)
        btn_fast.draw(screen)
        btn_intermediate.draw(screen)
        btn_slow.draw(screen)

        input_box.draw(screen)

        pygame.display.update()
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
