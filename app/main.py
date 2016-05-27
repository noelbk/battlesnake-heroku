# encoding: utf-8
from __future__ import unicode_literals
import bottle
import os
import logging
import random
import os

from . import snake

LOG = logging.getLogger(__name__)

snake_name = os.environ.get('SNAKE_NAME', 'Nöl')
snake_color = os.environ.get('SNAKE_COLOR', '#fe642e')
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
        'color': snake_color,
        'head_url': head_url()
    }

    LOG.warn("index ret=%s", ret)

    return ret


@bottle.post('/start')
def start():
    data = bottle.request.json

    return {
        'name': snake_name,
        'color': snake_color,
        'taunt': 'Nol!',
        'head_url': head_url()
    }


@bottle.post('/move')
def move():
    data = bottle.request.json

    move = snake.battlesnake_move(data, snake_name)

    return {
        'move': move,
        'taunt': 'Nol!',
    }


@bottle.post('/end')
def end():
    data = bottle.request.json

    return {
        'taunt': 'Nol!',
    }


# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
