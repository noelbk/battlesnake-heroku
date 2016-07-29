import math
from app import snake

MAX_HEALTH = 100

class BoardStruct(object):
    turn = 0
    snakes = []
    food = []


class SnakeApi(object):
    def begin(self, arenaStruct):
        pass

    def end(self):
        pass

    def move(self, boardStruct, snakeState):
        pass

class SnakeState(object):
    def __init__(self, snake_api):
        self.snake_api = snake_api
        self.name = None
        self.health = HEALTH_MAX
        self.body = []
        self.last_eaten = None

class BattlesSnakeArena(object):
    def __init__(self, width, height, snakes):
        self.board = Board(width, height, CELL_TYPE_SPACE)
        self.snakes = snakes
        self.turn = 0

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
            snake.health = MAX_HEALTH

        # 4 foods at the center
        x0 = int(self.board.xmax/2)
        y0 = int(self.board.ymax/2)
        for dx, dy in (
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
            ):
            self.board[self.board.pos(x0+dx, y+dy)] = CELL_TYPE_FOOD

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

        for snake in self.snakes:
            coords = []
            data['snakes'].append({
                'name': snake.name,
                'last_eaten': snake.last_eaten,
                'coords': coords,
                })
            for pos in snake.body:
                coords.append(board.coords(pos))

        for snake in self.snakes:
            move_name = snake.move(data)
            move = MOVES[move_name]
            x, y = snake.body[0]
            x += move.dx
            y += move.dy
            if x < 0 or >= board.xmax or y < 0 or y >= board.ymax:
                # death!
                pass

            pos = board.index(x, y)
            if board[pos] == SPACE:
                # pop the last segment
                snake.pos.remove()
            elif board[pos] == FOOD:
                snake.health = MAX_HEALTH
                snake.length += 1
            else:
                # death!
                pass

        # add random food to board
        pos = board.index(randint(self.board.xmax), randint(self.board.ymax))
        if board[pos]:
            board[pos] = FOOD


    def run(self):
        while(True):
            self.move()
            self.print()
