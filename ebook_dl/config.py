#!/usr/bin/python3
# -*- coding:utf-8 -*-

import logging

__all__ = ['get', 'assign', 'init']

def config_logging():
    level = logging.WARNING
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)-8s | %(name)s: %(msg)s ',
        datefmt='%H:%M:%S',
    )


def init():
    global opts
    opts = {
        'keyword': '',
        'fake_headers': {
            'User-Agent': 'Mozilla/5.0 3578.98 Safari/537.36'
        }
    }


def get(key):
    return opts.get(key, '')


def assign(key, value):
    opts[key] = value