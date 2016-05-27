#! /usr/bin/env python
import string
import logging
import collections

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

MOVES = (
    (-1,  0, 'left'),
    ( 1,  0, 'right'),
    ( 0,  1, 'down'),
    ( 0, -1, 'up'),
    )

class DEFAULT(): pass
def isdefault(x):
    return isinstance(x, DEFAULT)

STARVATION_TURNS = 100
CELL_BLANK = ' '
CELL_FOOD = '+'
CELL_GOLD = '*'
CELL_WALL = '#'
CELL_SNAKES = set(string.ascii_letters)
CELL_SNAKE_HEADS = string.ascii_uppercase
CELL_TYPE_MY_HEAD = 'A'

def cell_snake_body(snake_id):
    return snake_id.lower()

class CellClass(object):
    def __init__(self, cell_type):
        self.cell_type = cell_type

    def is_member(self, cell):
        return cell in self.cell_type

    def is_opaque(self, cell):
        return cell == CELL_WALL or cell in CELL_SNAKES

CELL_CLASS_SPACE = CellClass(CELL_BLANK)
CELL_CLASS_FOOD = CellClass(CELL_FOOD)
CELL_CLASS_DEATH = CellClass(CELL_SNAKES | set((CELL_WALL,)))
CELL_CLASS_HEADS = CellClass(set(CELL_SNAKE_HEADS) - set((CELL_TYPE_MY_HEAD,)))
CELL_CLASS_ME = CellClass(set('aA'))
CELL_CLASS_GOLD = CellClass(CELL_GOLD)

class Board():
    def __init__(self, xmax, ymax, board=None):
        self.starvation = 1.0
        self.xmax = xmax
        self.ymax = ymax
        if board is None:
            self.board = self.new_board()
        else:
            self.board = self.loads(board)
        self.neighbours = self.cell_neighbours()

    @classmethod
    def from_lines(cls, *lines):
        return cls(len(lines[0]), len(lines), "\n".join(lines) + "\n")

    def cell_idx(self, x, y):
        return y*self.xmax + x

    def get(self, x, y, board=None):
        if board is None:
            board = self.board
        return board[self.cell_idx(x, y)]

    def put(self, x, y, thing, board=None):
        if board is None:
            board = self.board
        board[self.cell_idx(x, y)] = thing

    def cell_neighbours(self):
        neighbours = []

        for x, y, i in self.board_iter():
            adj = []
            for dx, dy, move_name in MOVES:
                x1 = x + dx
                y1 = y + dy
                if x1 >= 0 and x1 < self.xmax and y1 >= 0 and y1 < self.ymax:
                    adj.append((self.cell_idx(x1,y1), move_name))
            neighbours.append(adj)
        return neighbours

    def dumps(self, board=None):
        if board is None:
            board = self.board
        s = ""
        for x, y, i in self.board_iter():
            #if x > 0:
            #    s += " "
            s += str(board[i])
            if x == self.xmax-1:
                s += "\n"
        return s

    def new_board(self, val=DEFAULT):
        if val is DEFAULT:
            val = CELL_BLANK
        return [val] * (self.xmax * self.ymax)

    def loads(self, s):
        sit = iter(s)
        board = self.new_board()
        for x, y, i in self.board_iter():
            board[i] = sit.next()
            if x == self.xmax-1:
                assert sit.next() == '\n'
        self.board = board
        return board

    def board_iter(self):
        i = 0
        for y in range(self.ymax):
            for x in range(self.xmax):
                yield x, y, i
                i += 1

    def find(self, cellval):
        for x, y, i in self.board_iter():
            if self.board[i] == cellval:
                yield x, y, i

    def smell(self, cell_class):
        """make a smell map from the board"""
        todo = []
        board = self.board
        for x, y, i in self.board_iter():
            if cell_class.is_member(board[i]):
                todo.append(i)

        smell_map = self.new_board(None)
        level = 0
        while todo:
            todo_next = []
            for idx in todo:
                if smell_map[idx] is not None or (cell_class.is_opaque(board[idx]) and not cell_class.is_member(board[idx])):
                    continue
                smell_map[idx] = level
                for move_idx, _move_name in self.neighbours[idx]:
                    todo_next.append(move_idx)
            level += 1
            todo = todo_next
        for i, value in enumerate(smell_map):
            if smell_map[i] is not None:
                smell_map[i] = float(smell_map[i])/level

        return smell_map, level

    def smell_food(self):
        return self.smell(CELL_CLASS_FOOD)

    def smell_gold(self):
        return self.smell(CELL_CLASS_GOLD)

    def smell_death(self):
        return self.smell(CELL_CLASS_HEADS)

    def smell_space(self):
        """see which direction leads to the most open space"""
        todo = collections.deque()
        board = self.board

        x, y, idx = next(self.find(CELL_TYPE_MY_HEAD))
        todo.append((idx, None))

        space_map = self.new_board(None)
        score_idx = {}
        while todo:
            move_idx, start_move_name = todo.popleft()
            for idx, move_name in self.neighbours[move_idx]:
                prev_move_name = start_move_name
                if space_map[idx] is not None or CELL_CLASS_SPACE.is_opaque(board[idx]):
                    continue

                if not prev_move_name:
                    prev_move_name = move_name
                    score_idx[prev_move_name] = idx
                    space_map[idx] = 0
                else:
                    space_map[idx] = prev_move_name[0]

                space_map[score_idx[prev_move_name]] += 1
                todo.append((idx, prev_move_name))

        # normalize to 0..1
        max_space = 0
        if score_idx:
            max_space = max(space_map[idx] for idx in score_idx.values())
            for idx in score_idx.values():
                space_map[idx] = float(space_map[idx]) / max_space

        return space_map, max_space

    def score(self, cell, food, death, space):
        """highest score wins!

        food:   0 => next to food
        death:  1 => next move is death
        space:  1 => most open space
        """

        if CELL_CLASS_DEATH.is_member(cell):
            score = None
        else:
            score_food = 0
            if food is not None:
                score_food = 4.0 * self.starvation * (1.0 - food)
            score_space = 0
            if self.starvation < 0.8:
                if space is not None:
                    score_space = space
            score_death = 0
            if death is not None and death < 2:
                score_death = -10
            score = score_death + score_food + score_space
            LOG.debug("score=%.2f starvation=%0.3f score_death=%.3f + score_food=%.3f + score_space=%.3f food=%s",
                      score, self.starvation, score_death, score_food, score_space, food)
        return score

    def move(self):
        _x, _y, head_idx = next(self.find(CELL_TYPE_MY_HEAD))

        food, food_max = self.smell_food()
        death, death_max = self.smell_death()
        space, space_max = self.smell_space()

        best_move = MOVES[0][-1]
        best_score = None
        for move_idx, move_name in self.neighbours[head_idx]:
            cell = self.board[move_idx]
            if death[move_idx] is None:
                death_abs = None
            else:
                death_abs = death[move_idx] * death_max
            score = self.score(cell,
                               food[move_idx],
                               death_abs,
                               space[move_idx])

            LOG.debug("score=%s move_name=%-5s cell=%s starvation=%s food=%s death=%s space=%s",
                      score, move_name, cell, self.starvation,
                      food[move_idx], death_abs, space[move_idx])


            if score is None:
                continue

            if best_score is None or score > best_score:
                best_move = move_name
                best_score = score

        LOG.debug("head=%s best_move=%s", head_idx, best_move)
        LOG.debug("board\n%s", self.dumps())

        return best_move

def battlesnake_board(data, snake_name):
    LOG.debug("battlesnake_board snake_name=%s", snake_name)

    ymax = len(data['board'])
    xmax = len(data['board'][0])

    board = Board(xmax, ymax)

    debug_data = data.copy()
    del debug_data['board']
    LOG.debug("battlesnake_board data=%s", debug_data)

    for x, y in data['food']:
        board.put(x, y, CELL_FOOD)

    # make a board with all snakes as Aaaa Bbbbb Cccc.... where Aaaaa is me
    snake_ids = iter(CELL_SNAKE_HEADS)
    my_id = next(snake_ids)
    for snake in data['snakes']:
        if snake['name'] == snake_name:
            snake_id = my_id
            try:
                board.starvation = float(data['turn'] - snake['last_eaten']) / STARVATION_TURNS
            except KeyError as e:
                LOG.warn("KeyError: %s", e)
                board.starvation = .5
        else:
            snake_id = next(snake_ids)
        for x, y in snake['coords']:
            if board.get(x, y) == CELL_BLANK:
                board.put(x, y, snake_id)
            snake_id = cell_snake_body(snake_id)

    return board

def battlesnake_move(data, snake_name):
    return battlesnake_board(data, snake_name).move()
