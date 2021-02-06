#!/usr/bin/python3
# -*- conding:utf-8 -*-

import os
import sys


def start():
	sys.path.insert(1, os.getcwd())
	if sys.version_info[0] == 3:
		import ebook_dl
		ebook_dl.run()
	else:
		print('This program uses python3 only.')


if __name__ == '__main__':
	start()