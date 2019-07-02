FROM python:3.7.2-stretch

ENV TIME_ZONE=Asia/Shanghai CODE_DIR=/code

RUN ln -snf /usr/share/zoneinfo/$TIME_ZONE /etc/localtime \
    && echo $TIME_ZONE > /etc/timezone \
    && apt update \
    && apt install -y swig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR $CODE_DIR
COPY ./ $CODE_DIR/
RUN pip install -i https://pypi.douban.com/simple -r requirements.txt
