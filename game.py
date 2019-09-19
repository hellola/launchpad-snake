import launchpad_py
import time
import random

quit = False
grid_size = 8

class Button:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = 10 
    
    def press(self):
        return

    def next_color(self):
        self.color += 1
        self.color = self.color % 128

class Pos:
    def __init__(self, x,y):
        global grid_size
        self.x = x % grid_size
        self.y = y % grid_size

    @classmethod
    def random(cls):
        global grid_size
        x = random.randint(0, grid_size - 1)
        y = random.randint(0, grid_size - 1)
        return Pos(x, y)

    def __str__(self):
        return f"{self.x}, {self.y}"

    def left_by(self, count):
        return Pos(self.x - count, self.y)

    def equals(self, pos):
        return self.x == pos.x and self.y == pos.y

    def in_direction(self, direction):
        if direction == "right":
            return Pos(self.x + 1, self.y)
        elif direction == "left":
            return Pos(self.x - 1, self.y)
        elif direction == "up":
            return Pos(self.x, self.y - 1)
        elif direction == "down":
            return Pos(self.x, self.y + 1)

    def is_above(self, pos):
        return self.x == pos.x and self.y < pos.y
    
    def is_below(self, pos):
        return self.x == pos.x and self.y > pos.y

    def is_left_of(self, pos):
        return self.y == pos.y and self.x < pos.x

    def is_right_of(self, pos):
        return self.y == pos.y and self.x > pos.x

class Snake:
    def __init__(self, world):
        self.world = world
        self.direction = "right"
        self.delta = 0
        self.head = self.build_body(4)
        self.consuming = False
        self.snake_speed_delta = 1.0

    def is_consuming(self):
        return self.consuming

    def pos(self):
        return self.head.pos()

    def consume(self):
        tail = self.head.tail()
        block = Block(self, tail, tail.ghost_pos)
        self.consuming = True
        tail.attach(block)

    def build_body(self, number):
        previous = None
        start = Pos(5, 5)
        for i in range(number):
            block = Block(self, previous, start.left_by(i))
            if previous != None:
                previous.attach(block)
            previous = block
        return previous.head()
            
    def required_delta(self):
        return 2.0 / self.head.size()

    def update(self, delta):
        self.delta += delta
        self.head.update_color()

        if self.delta > self.required_delta():
            self.head.update(self.world, self.direction)
            self.delta = 0

    def press(self, pos):
        if pos.is_above(self.head.pos()):
            self.direction = "up"
        elif pos.is_below(self.head.pos()):
            self.direction = "down"
        elif pos.is_left_of(self.head.pos()):
            self.direction = "left"
        elif pos.is_right_of(self.head.pos()):
            self.direction = "right"

class Consumable:
    def __init__(self, pos):
        self._pos = pos
        self.consumed = False
    def pos(self):
        return self._pos
    def consume(self, consumer):
        print("consuming!", consumer)
        self.consumed = True
        consumer.consume()
    def update(self, world):
        if not self.consumed:
            world.at(self._pos).color = launchpad_py.LaunchpadMk2.COLORS["white"]

        
class Block:
    def __init__(self, snake, prev, pos):
        self.nxt = None
        self.snake = snake
        self.prev = prev
        self._pos = pos
        self.ghost_pos = pos

    def size(self):
        current = self.head()
        count = 0
        while (not current.is_tail()):
            count += 1
            current = current.nxt
        return count

    def is_consuming(self):
        return self.snake.is_consuming()

    def update(self, world, direction):
        world.reset_at(self._pos)
        self.update_color()
        if self.is_head():
            self.set_pos(self.pos().in_direction(direction))
        else:
            self.set_pos(self.prev.ghost_pos)
        if (not self.is_tail()):
            self.nxt.update(world, direction)

    def set_pos(self, new_pos):
        self.ghost_pos = self._pos
        self._pos = new_pos
    
    def pos(self):
        return self._pos
    
    def update_color(self):
        world.at(self._pos).color = self.color()
        
    def color(self):
        color = None
        if self.is_head():
            if self.is_consuming():
                color = 20
            else:
                color = launchpad_py.LaunchpadMk2.COLORS["red"]
        else:
            color = launchpad_py.LaunchpadMk2.COLORS["green"]
        return color

    def is_tail(self):
        return self.nxt == None

    def is_head(self):
        return self.prev == None

    def head(self):
        if self.is_head():
            return self
        else:
            return self.prev.head()
    
    def tail(self):
        if self.is_tail():
            return self
        else:
            return self.nxt.tail()
    
    def attach(self, block):
        tail = self.tail()
        tail.nxt = block
        block.prev = tail

class World:
    def __init__(self):
        self.buttons = []
        self.button_map = {}
        self.build_buttons_list()
        self.consumables = self.generate_consumables(1)
        self.last_handled_at = Pos(0,0)
        self.snake = None

    def generate_consumables(self, count):
        return [Consumable(Pos.random()) for x in range(count)]

    def build_buttons_list(self):
        x_axis = range(0,9)
        y_axis = range(0,9)
        for y in y_axis:
            for x in x_axis:
                button = Button(x,y)
                self.buttons.append(button)
                self.button_map[f"{x}{y}"] = button

    def reset_at(self, pos):
        self.at(pos).color = self.default_color

    def button_at(self, x, y):
        return self.button_map[f"{x}{y}"]
    
    def at(self, pos):
        return self.button_map[f"{pos.x}{pos.y}"]

    def render(self):
        for button in self.buttons:
            self.lp.LedCtrlXYByCode(button.x, button.y, button.color)

    def process(self, delta):
        event = self.lp.ButtonStateXY()
        global quit
        if event != []:
            x = event[0]
            y = event[1]
            if event[2] == 0:
                pressed = False
            else:
                self.snake.press(Pos(x,y))
                self.button_at(x,y).press()
                print(f"you pressed: {x}, {y}")
                if x == 8 and y == 8:
                    quit = True

    def update(self, delta):
        self.handle_consumables()
        self.snake.update(delta)
    
    def handle_consumables(self):
        if not self.last_handled_at.equals(self.snake.pos()):
            self.last_handled_at = self.snake.pos()
            consumed = []
            for consumable in self.consumables:
                consumable.update(self)
                if self.snake.pos().equals(consumable.pos()):
                    print(f"yum: {len(self.consumables)}")
                    consumable.consume(self.snake)
                    consumed.append(consumable)
            for consumable in consumed:
                self.consumables.remove(consumable)
            print("consumed:", len(consumed))
            new_consumables = self.generate_consumables(len(consumed))
            self.consumables.extend(new_consumables)
        else:
            self.snake.consuming = False

    def start(self):

        self.lp = launchpad_py.LaunchpadMk2()
        opened = self.lp.Open()
        if not(opened):
            return "Not able to use device"
        self.lp.Reset()

        self.snake = Snake(self)
        self.default_color = 10

        self.lp.LedAllOn(self.default_color)
        global quit
        last_time = time.time()
        while (not quit):
            delta = time.time() - last_time 
            last_time = time.time()
            self.process(delta)
            self.update(delta)
            self.render()

        self.lp.LedAllOn(self.lp.COLORS["black"])
        self.lp.Close()
        return "opened"



world = World()
world.start()