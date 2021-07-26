#!/usr/bin/python3
# Script for finding reduntant backups
# Gotsko Nikita 2021-07-24
#
# Policy:
#   current and previous month: 3 per day
#   current year, older than 2 month: 2 per day
#   current year, older than 3 month: 1 per day
#   previous year: 1 per month
#   older than 1 year: 1 per quarter

# TODO: older than 1 year
# TODO: accept patterns for backups
# TODO: improve args

import os
import logging
import argparse
import re
import datetime
from datetime import datetime, timedelta


class BackupItem:
    # regex as key, 1989 C as value
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    patterns = {
        r'(?P<day>\d{2})-(?P<month>\S{3})-(?P<year>\d{4})-(?P<hour>\d{2}):(?P<minute>\d{2})' : '%d-%b-%Y-%H:%M',
        r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})_(?P<hour>\d{2})-(?P<minute>\d{2})' : '%Y-%m-%d_%H-%M',
    }

    def __init__(self, path):
        self.path = path
        self.dt = self._get_date(os.path.basename(path))
        self.name = self._get_name(os.path.basename(path))
    
    def _get_date(cls, fname):
        for pattern in cls.patterns:
            match = re.search(pattern, fname)
            if match:
                dt = datetime.strptime(match.group(), cls.patterns[pattern])
                logging.debug(f'Parsed date for {fname}: {dt}')
                return dt
        raise NotImplementedError
    
    def _get_name(self, fname):
        delimeter = '-'
        return fname.split(delimeter)[0]


def find_reduntant(series, start, end, period, amount):
    reduntant = []
    filtered = [item for item in series if start < item.dt < end]
    current = start
    while current < end:
        current_filtered = [item for item in filtered if current < item.dt < current + period]
        reduntant.extend(current_filtered[amount:])
        for item in current_filtered[amount:]:
            logging.debug(f'found reduntant item [{item.name}]{item.path}, {current} < {item.dt} < {current + period}')
        current = current + period
    
    return reduntant

def find_series(path):
    logging.debug(f'listing items in {path}')
    items = [BackupItem(os.path.join(path, name)) for name in os.listdir(path) \
        if any([re.search(pattern, name) for pattern in BackupItem.patterns.keys()])]
    
    return items
    
def main(args):
    parse_datetimes(args) # arg by ref, modifying state of args
    series = find_series(args.dir)
    backups = {}
    for item in series:
        if item.name not in backups.keys(): backups[item.name] = []
        backups[item.name].append(item)
    
    for name, items in backups.items():
        reduntant = find_reduntant(items, args.since, args.to, args.period, args.amount)
        for item in reduntant:
            print(item.path)

def parse_timedelta(string):
    '''
        courtecy of virhilo
        https://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string

        returns timedelta from string
    '''
    match = re.match(r'((?P<weeks>\d+?)w)?((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?', string)
    if not match:
        raise ValueError(f'failed to parse relative timedelta string, "{string}"')

    parts = match.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def parse_datetimes(args):
    try:
        dt = datetime.strptime(args.since, '%Y-%m-%d')
        args.since = dt
    except ValueError as err:
        logging.warning(f'failed to parse start date using ISO 8601 format(YYYY-MM-DD), "{args.since}"')
        td = parse_timedelta(args.since)
        # TODO: make as argument
        args.since = datetime.now().replace(hour=0, minute=0, second=0) - td
        logging.info(f'relative start date {td} is {args.since}')

    if not args.to:
        args.to = datetime.now()
    else:
        try:
            dt = datetime.strptime(args.to, '%Y-%m-%d')
            args.to = dt
        except ValueError as err:
            logging.warning(f'failed to parse end date using ISO 8601 format(YYYY-MM-DD), "{args.to}"')
            td = parse_timedelta(args.to)
            args.to = datetime.now() - td
            logging.info(f'relative end date {td} is {args.to}')
    
    args.period = parse_timedelta(args.period)


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
    parser.add_argument("--amount", help="Amount of backups to be kept per --period(default 1d), default is 1", type=int, default=1)
    parser.add_argument("--period", help="Timedelta for counting --amount of backups, default is 1d", default="1d")
    parser.add_argument("--since", help="Start date, accepts ISO 8601 format(YYYY-MM-DD) or relative shortcuts(0w0d0h0m0s), default is 30d old", default="30d")
    #parser.add_argument("--first-day", help="Move --start date to 1st day of month", action='store_true')
    parser.add_argument("--to", help="End date, in ISO 8601 format(YYYY-MM-DD), or relative shortcuts(0w0d0h0m0s), default now()")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    setup_logging(args)
    main(args)
