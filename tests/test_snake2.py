#! /usr/bin/env python
# Copyright 2016 Noel Burton-Krahn <noel@burton-krahn.com>

import unittest
from app import snake2 as snake

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class TestSnake(unittest.TestCase):
    def test_loads(self):
        board = snake.Board(10, 10)
        boardstr = (
            #0123456789
            "          \n" # 0
            "    # C   \n" # 1
            "    # c   \n" # 2
            "  A ####  \n" # 3
            "  a    bbb\n" # 4
            "  a  * b b\n" # 5
            "  a    b b\n" # 6
            "  aaa  b b\n" # 7
            "  ##   B b\n" # 8
            "  *   bbbb\n" # 9
            )
        board.loads(boardstr)
        self.assertEqual(boardstr, board.dumps())

        self.assertEqual(set(board.find('A')), set([(2,3,32)]))
        self.assertEqual(set(board.find('*')), set([(5,5,55), (2,9,92)]))

        self.assertEqual(set(board.neighbours[0]), set([(1, 'right'), (10, 'down')]))
        self.assertEqual(set(board.neighbours[11]), set([(1, 'up'), (10, 'left'), (12, 'right'), (21, 'down')]))

        smells = [
            board.smell_death()[0],
            board.smell_food()[0],
            board.smell_gold()[0],
            board.smell_space()[0],
        ]

        x,y,head = next(board.find('A'))
        for adj in board.neighbours[head]:
            args = [smell[adj[0]] for smell in smells]
            #score = smell_score(*args)

    def test_smell(self):
        board = snake.Board.from_lines(
            "  # + ",
            "A ##  ",
            "a+   B",
            )

        self.assertEqual(board.dumps(),
                         "  # + \n"
                         "A ##  \n"
                         "a+   B\n")

        self.assertEqual(board.smell_food(),
                         ([x if x is None else float(x)/5 for x in [
               3,    2, None,    1,    0,    1,
            None,    1, None, None,    1,    2,
            None,    0,    1,    2,    2, None,
            ]],5))

        self.assertEqual(board.smell_death(),
                         ([x if x is None else float(x)/9 for x in
            [
               7,    6, None,    4,    3,    2,
            None,    5, None, None,    2,    1,
            None,    4,    3,    2,    1,    0,
            ]], 9))

    def test_space(self):
        board = snake.Board.from_lines(
            " B    ",
            "    # ",
            "  A   ",
            "  a   ",
            "      ",
            )

        self.assertEqual(
            board.dumps(),
            " B    \n"
            "    # \n"
            "  A   \n"
            "  a   \n"
            "      \n"
            )

        _ = None
        self.assertEqual(
            board.smell_space(),
            ([
            'l',   _, 'u', 'r', 'r', 'r',
            'l', 'l',   2.0/14, 'r',   _, 'r',
            'l',  10.0/14,   _,  14.0/14, 'r', 'r',
            'l', 'l',   _, 'r', 'r', 'r',
            'l', 'l', 'l', 'r', 'r', 'r',
            ],14))
