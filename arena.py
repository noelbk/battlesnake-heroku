import math
import collections
import threading

from app import snake
from snake import board


def SnakeProxy(object):
    def move(self, arena, name, last_state):
        """move_name, name, next_state = move(arena, name, last_state)"""

class SnakeState(object):
    def __init__(self, snake_proxy):
        self.snake_proxy = snake_proxy
        self.name = None
        self.health = HEALTH_MAX
        self.body = []
        self.last_eaten = None

    def move(self, arena, queue):
        move_name, self.last_state = self.snake_proxy.move(arena, self.last_state)
        queue.append((self, move_name))

class BattlesSnakeArena(object):
    MAX_HEALTH = 100

    def __init__(self, width, height):
        self.board = Board(width, height, CELL_TYPE_SPACE)
        self.snakes = snakes
        self.turn = 0

    self add_snake(self, snake_proxies):
        self.snakes.append()
        pass

    def init(self):
        self.turn = 0

        # init: all snakes start around the center
        for i, snake in enumerate(self.snakes):
            theta = i/n * 2 * math.pi
            r = self.board.xmax/4
            x = int(r * math.cos(theta)) + self.board.xmax/2
            y = int(r * math.sin(theta)) + self.board.ymax/2
            pos = self.board.index(x, y)
            snake.body = [pos] * 3
            snake.health = self.MAX_HEALTH

        # 4 foods at the center
        x0 = int(self.board.xmax/2)
        y0 = int(self.board.ymax/2)
        for dx, dy in (
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
            ):
            self.board[self.board.pos(x0+dx, y+dy)] = board.CELL_TYPE_FOOD

    def move(self):
        self.turn += 1

        # make the battlesnake data structure
        data = {
            'turn': self.turn,
            }

        data['board'] = []
        pos = 0
        for y in range(self.board.ymax):
            row = []
            data['board'].append(row)
            for x in range(self.board.xmax):
                val = self.board[pos]
                row.append(val)
                pos += 1

        coords = []
        data['snakes'].append({
            'name': snake.name,
            'last_eaten': snake.last_eaten,
            'coords': coords,
            })
        for pos in snake.body:
            coords.append(board.coords(pos))

        def snake_move(snake, data, queue):
            move_name = snake.move(data)
            queue.put((snake, move_name))

        # give each snake its own thread to move
        queue = Queue.Queue()
        snake_threads = {}
        for snake in self.snakes:
            snake_thread = threading.Thread(target=snake_move, args=(snake, data, queue), name=snake.name)
            snake_thread.daemon = True
            snake_thread.start()
            snake_threads[snake] = snake_thread

        # collect all the  snake results
        while snake_threads:
            snake, move_name = queue.get(True)
            snake_threads[snake].join()
            del snake_threads[snake]

            # do the move
            move = board.MOVES[move_name]
            x, y = snake.body[0]
            x += move.dx
            y += move.dy
            if x < 0 or >= board.xmax or y < 0 or y >= board.ymax:
                # death!
                pass

            pos = board.index(x, y)
            if board[pos] == CELL_TYPE_SPACE:
                # pop the last segment
                snake.pos.remove()
            elif board[pos] == CELL_TYPE_FOOD:
                snake.health = self.MAX_HEALTH
                snake.length += 1
            else:
                # death!
                pass

        # add random food to board
        pos = randint(self.board.xmax * self.board.ymax)
        if board[pos]:
            board[pos] = CELL_TYPE_FOOD


    def run(self):
        while(True):
            self.move()
            self.print()
