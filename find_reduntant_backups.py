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
import re
import datetime
from datetime import datetime, timedelta

pattern_date = r'(?P<name>.*)-(?P<day>\d\d)-(?P<month>\S{3})-(?P<year>\d\d\d\d)-(?P<hour>\d\d):(?P<minute>\d\d).*'

def parse_filenames(path):
    logging.debug(f'listing files in {path}')
    files = [item for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))]
    backups = {}
    for fpath in files:
        logging.debug(f'testing {fpath}')
        match = re.search(pattern_date, fpath)
        if match:
            name, day, month, year, hour, minute = match.groups()
            logging.info(f'Matched [{name}] {fpath}: {match.groups()}')
            dt = datetime.strptime(''.join([day, month, year, hour, minute]), '%d%b%Y%H%M')
            if name not in backups.keys(): backups[name] = {}
            backups[name][dt] = fpath

def filter_current(path):
    parse_filenames(path)
    

def main(args):
    if args.current: filter_current(args.dir)

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
    parser.add_argument("--current", help="List backups reduntant backups from current 2 month", action='store_true')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    setup_logging(args)
    main(args)
