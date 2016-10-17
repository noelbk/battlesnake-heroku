FROM ubuntu
MAINTAINER Noel Burton-Krahn <noel@burton-kahn.com>
# TAG ubuntu-heroku
WORKDIR /app
ADD etc /etc
ADD . .
ADD requirements.* ./
RUN apt-key add /etc/apt/heroku.release.key
RUN apt-get update && apt-get -y install \
  make \
  python \
  python-pip \
  python-dev \
  ncurses-dev \
  mongodb \
  heroku \
  curl \
  tcpdump
# to install heroku commandline
RUN heroku --help
RUN make install
RUN pip install --upgrade pip && pip install --upgrade $(cat requirements.txt)
CMD make run SNAKE_NAME="docker-$HOSTNAME"
