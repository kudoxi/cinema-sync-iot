import logging
from logging.config import dictConfig

def logger(name=''):
    dictConfig({
        "version": 1,
        "formatters": {
            "f": {"format": "[%(asctime)s %(levelname)-8s %(name)-8s]: %(message)s"}
        },
        "handlers": {
            "h": {"formatter": "f", "class": "logging.StreamHandler"}
        },
        "root": {"handlers": ["h"], "level": "DEBUG"}
    })
    logging.basicConfig(format="[%(asctime)s %(levelname)-8s %(name)-8s]: %(message)s",
                        datefmt="%H:%M:%S",
                        filename="receive.log",
                        level=logging.DEBUG)
    return logging

