from collections import namedtuple, deque
import string
import logging

LOG = logging.getLogger(__name__)

Cell = namedtuple('Cell', ['index', 'value'])

Move = namedtuple('Move', ['dx', 'dy', 'name'])
MOVES = [
    Move(-1,  0, 'left'),
    Move( 0, -1, 'up'),
    Move( 1,  0, 'right'),
    Move( 0,  1, 'down'),
    ]
INF = float('inf')

STARVATION_TURNS = 100
CELL_TYPE_SELF = 'A'
CELL_TYPE_ENEMY = set(string.ascii_uppercase) - set(CELL_TYPE_SELF)
CELL_TYPE_SPACE = ' '
CELL_TYPE_FOOD = '*'

class CellType(object):
    def __init__(self, char_set):
        self.char_set = char_set

    def is_member(self, val):
        return val in self.char_set

    def is_opaque(self, val):
        return not self.is_member(val) and val not in (CELL_TYPE_SPACE, CELL_TYPE_FOOD, CELL_TYPE_SELF)

CellTypeSelf  = CellType(CELL_TYPE_SELF)
CellTypeEnemy = CellType(CELL_TYPE_ENEMY)
CellTypeFood  = CellType(CELL_TYPE_FOOD)

class Board(list):
    """A board is a 2-d array of values"""

    def __init__(self, xmax, ymax, val=None):
        super(Board, self).__init__()

        self.xmax = xmax
        self.ymax = ymax
        if not callable(val):
            f = lambda x, y: val
        else:
            f = val

        for y in range(ymax):
            for x in range(xmax):
                self.append(f(x, y))

        self.ttl = 10

    @classmethod
    def load_strs(cls, *strs):
        ymax = len(strs)
        xmax = len(strs[0])
        vals = iter("".join(strs))
        return Board(xmax, ymax, lambda x, y: next(vals))


    def index(self, x, y):
        """convert (x,y) coordinates to an integer index in my array"""
        return y * self.xmax + x

    def put(self, x, y, val):
        self[self.index(x, y)] = val

    def coords(self, index):
        """return the x, y coordinates of index"""
        return index % self.xmax, index / self.xmax

    def __iter__(self):
        """iterate over all my cell indexes and values"""
        for index in range(self.xmax * self.ymax):
            yield Cell(index, self[index])

    def head(self):
        for cell in self:
            if CellTypeSelf.is_member(cell.value):
                return cell

    def neighbours(self, index):
        """return all (index, move_name) adjacent to index"""
        x, y = self.coords(index)
        for move in MOVES:
            x1 = x + move.dx
            y1 = y + move.dy
            if x1 >= 0 and x1 < self.xmax and y1 >= 0 and y1 < self.ymax:
                yield Cell(self.index(x1, y1), move.name)

    def board(self, value=None):
        """make a new board with my dimensions"""
        return Board(self.xmax, self.ymax, value)

    def smell(self, cell_type):
        """make a board where the values are the number of moves from
        each cell to the nearest cell_type"""

        # by default, everything is infinite moves away
        smell = self.board(INF)

        # start with all cells in cell_type
        todo = deque()
        for cell in self:
            if cell_type.is_member(cell.value):
                todo.append((cell, 0.0))

        # keep adding neighbours at increasing distance
        max_dist = 0
        while todo:
            cell, dist = todo.popleft()

            # stop if this cell is already hit or is opaque
            if smell[cell.index] != INF or cell_type.is_opaque(self[cell.index]):
                continue

            smell[cell.index] = dist
            if dist > max_dist:
                max_dist = dist
            for cell in self.neighbours(cell.index):
                todo.append((cell, dist+1))

        return smell, max_dist

    def smell_food(self):
        return self.smell(CellTypeFood)

    def smell_enemy(self):
        return self.smell(CellTypeEnemy)

    def smell_self(self):
        return self.smell(CellTypeSelf)

    def smell_space(self):
        """see which move next to my head leads to the most open space"""
        todo = deque()
        space_map = self.board()

        head = self.head()
        todo.append((Cell(head.index, None), 0))

        while todo:
            prev_cell, dist = todo.popleft()
            for next_cell in self.neighbours(prev_cell.index):
                if space_map[next_cell.index] is not None or CellTypeSelf.is_opaque(self[next_cell.index]):
                    continue

                move_name = prev_cell.value
                if not move_name:
                    move_name = next_cell.value
                space_map[next_cell.index] = move_name

                todo.append((Cell(next_cell.index, move_name), dist+1))

        return space_map

    def move(self):
        food, food_max = self.smell_food()
        enemy, _enemy_max = self.smell_enemy()
        dist, _dist_max = self.smell_self()
        space = self.smell_space()

        head = self.head()

        space_by_move = {}
        for cell in space:
            # 1 point per cell, minus the likelihood that I'll meet an enemy there
            if not cell.value:
                continue
            if cell.value not in space_by_move:
                space_by_move[cell.value] = 0.0
            space_by_move[cell.value] += 1.0 - 1.0 / (max(enemy[cell.index], 1.0) * max(dist[cell.index], 1.0))
        if space_by_move:
            space_max = max(space_by_move.values())
            space_by_move = {k: v/space_max for k, v in space_by_move.items()}

        # make sure the closest food isn't too far away to eat
        closest_food = 1 + min([INF] + [food[move.index] for move in self.neighbours(head.index)])

        # now find the best move
        best_move = MOVES[0].name
        best_score = -INF
        for move in self.neighbours(head.index):
            if CellTypeSelf.is_opaque(self[move.index]):
                continue

            score = 0.0

            if enemy[move.index] <= 1:
                # bad!  Do not go where an enemy could move next
                score -= 4.0

            if self.ttl < 2 * closest_food:
                # I'm hungry, get food!
                score += 2.0 * (1.0 - (food[move.index] or 0)/food_max)

            # prefer open space
            score += space_by_move.get(move.value, 0.0)

            if score > best_score:
                best_move = move.value
                best_score = score

        return best_move

def battlesnake_move(data, snake_name):
    ymax = len(data['board'])
    xmax = len(data['board'][0])

    board = Board(xmax, ymax)

    debug_data = data.copy()
    del debug_data['board']
    LOG.debug("battlesnake_board snake_name=%s data=%s", snake_name, debug_data)

    for x, y in data['food']:
        board.put(x, y, CELL_TYPE_FOOD)

    # make a board with all snakes as Aaaa Bbbbb Cccc.... where Aaaaa is me
    my_id = CELL_TYPE_SELF
    enemy_ids = iter(CELL_TYPE_ENEMY)
    for snake in data['snakes']:
        if snake['name'] == snake_name:
            snake_id = my_id
            try:
                board.ttl = STARVATION_TURNS - (data['turn'] - snake['last_eaten'])
            except KeyError:
                board.ttl = 0
        else:
            snake_id = next(enemy_ids)

        for x, y in snake['coords']:
            board.put(x, y, snake_id)
            snake_id = snake_id.lower()

    return board.move()
