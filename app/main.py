# encoding: utf-8
from __future__ import unicode_literals
import os
import logging

import bottle

from . import snake

LOG = logging.getLogger(__name__)

SNAKE_NAME = os.environ.get('SNAKE_NAME', 'Shnözz')
SNAKE_TAUNT = "The sweet smell of victory"
SNAKE_COLOR = os.environ.get('SNAKE_COLOR', '#fe642e')
# '#%06x' % random.randint(0, 0xffffff)

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


def head_url():
    ret = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )
    LOG.debug("head_url=%s", ret)
    return ret

@bottle.get('/')
def index():
    LOG.warn("index")


    ret = {
        'color': SNAKE_COLOR,
        'head_url': head_url()
    }

    LOG.warn("index ret=%s", ret)

    return ret


@bottle.post('/start')
def start():
    _data = bottle.request.json

    return {
        'name': SNAKE_NAME,
        'color': SNAKE_COLOR,
        'taunt': 'Nol!',
        'head_url': head_url()
    }


@bottle.post('/move')
def move():
    data = bottle.request.json

    next_move = snake.battlesnake_move(data, SNAKE_NAME)

    return {
        'move': next_move,
        'taunt': SNAKE_TAUNT,
    }


@bottle.post('/end')
def end():
    _data = bottle.request.json

    return {
        'taunt': SNAKE_TAUNT,
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
