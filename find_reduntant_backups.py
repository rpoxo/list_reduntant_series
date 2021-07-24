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
from datetime import datetime, timedelta, date, time

pattern_date = r'(?P<name>.*)-(?P<day>\d\d)-(?P<month>\S{3})-(?P<year>\d\d\d\d)-(?P<hour>\d\d):(?P<minute>\d\d).*'

def parse_filenames(path, reduntant):
    logging.debug(f'listing files in {path}, excluding {reduntant}')
    files = [item for item in os.listdir(path) if os.path.isfile(os.path.join(path, item))]
    files = [fname for fname in files if os.path.join(path, fname) not in reduntant]
    logging.debug(f'files = {files}')
    backups = {}
    for fname in files:
        logging.debug(f'testing {fname}')
        match = re.search(pattern_date, fname)
        if match:
            name, day, month, year, hour, minute = match.groups()
            logging.info(f'Matched [{name}] {fname}: {match.groups()}')
            dt = datetime.strptime(''.join([day, month, year, hour, minute]), '%d%b%Y%H%M')
            if name not in backups.keys(): backups[name] = {}
            if year not in backups[name].keys(): backups[name][year] = {}
            if month not in backups[name][year].keys(): backups[name][year][month] = {}
            if day not in backups[name][year][month].keys(): backups[name][year][month][day] = {}

            backups[name][year][month][day][dt] = fname
    return backups

def filter_last(path, reduntant, daily_limit):
    '''
        Will display backups with more than 3 files per day for current and previous month(starting from 1st)
    '''

    today = datetime.combine(date.today(), time())
    last_month = today.replace(month=today.month-1)
    last_month_start = last_month.replace(day=1)

    backups = parse_filenames(path, reduntant)

    for name, years in backups.items():
        for year, months in years.items():
            for month, days in months.items():
                for day, datetimes in days.items():
                    filtered = [fname for dt, fname in datetimes.items() if dt > last_month_start]
                    if len(filtered) > daily_limit:
                        logging.warning(f'more than {daily_limit} backups found for {year}-{month}-{day}')
                        for fname in filtered[daily_limit:]:
                            logging.info(f'marking {fname} as reduntant')
                            return(os.path.join(path, fname))

def filter_older(path, reduntant, daily_limit, days):
    # NOTE: timedelta does not have month argument, as it needs to be datetime-aware for that
    td = timedelta(days=days)
    today = datetime.combine(date.today(), time())
    this_year = today.replace(month=1)
    this_year_start = this_year.replace(day=1)

    backups = parse_filenames(path, reduntant)

    for name, years in backups.items():
        for year, months in years.items():
            for month, days in months.items():
                for day, datetimes in days.items():
                    filtered = [fname for dt, fname in datetimes.items() if dt > this_year and dt < datetime.combine(date.today(), time()) - td]
                    if len(filtered) > daily_limit:
                        logging.warning(f'more than {daily_limit} backups found for {year}-{month}-{day}')
                        for fname in filtered[daily_limit:]:
                            logging.info(f'marking {fname} as reduntant, older than {datetime.combine(date.today(), time())} - {td} = {datetime.combine(date.today(), time()) - td}')
                            return(os.path.join(path, fname))
    

def main(args):
    reduntant = []
    if args.last: reduntant.append(filter_last(args.dir, reduntant, 3))
    elif args.older: reduntant.append(filter_older(args.dir, reduntant, 2, 60))
    elif args.old: reduntant.append(filter_older(args.dir, reduntant, 1, 90))
    else:
        reduntant.append(filter_last(args.dir, reduntant, 3))
        reduntant.append(filter_older(args.dir, reduntant, 2, 60))
        reduntant.append(filter_older(args.dir, reduntant, 1, 90))
    
    logging.debug(reduntant)
    logging.debug(set(reduntant))
    for fpath in set(reduntant):
        print(fpath)

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
    parser.add_argument("--last", help="List reduntant backups from last 2 month", action='store_true')
    parser.add_argument("--older", help="List reduntant backups older 2 month this year", action='store_true')
    parser.add_argument("--old", help="List reduntant backups older 3 month this year", action='store_true')
    parser.add_argument("--veryold", help="List reduntant backupsfrom previous year", action='store_true')
    parser.add_argument("--oldest", help="List reduntant backups older than year", action='store_true')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()
    setup_logging(args)
    main(args)
