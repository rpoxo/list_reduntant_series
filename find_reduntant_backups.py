#!/usr/bin/python3
# Script for finding reduntant backups
#
# Policy:
#   current and previous month: 3 per day
#   current year, older than 2 month: 2 per day
#   current year, older than 3 month: 1 per day
#   previous year: 1 per month
#   older than 1 year: 1 per quarter

import os
import logging
import argparse



def main(args):
    pass

def setup_logging(args):
    handlers = []
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-10s:%(funcName)s:%(message)s',
        #datefmt='%X',
        )

    sh = logging.StreamHandler()
    handlers.append(sh)
    
    levels = [
        logging.FATAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        ]
    try:
        level = levels[args.verbose]
    except IndexError:
        level = logging.DEBUG
    
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(level)

    logging.basicConfig(handlers=handlers, level=level)
    logging.log(level=logging.INFO, msg=f'Logging with {logging.getLevelName(level)} level')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="Path to directory with backups")
    parser.add_argument("-v", "--verbose", help="Set verbosity level", action='count', default=1)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    setup_logging(args)
    main(args)
