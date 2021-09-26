#! /usr/bin/env python3
import argparse
import json
import logging
import requests

from typing import Iterator


def get_parser() -> argparse.ArgumentParser:
    """The ArgumentParser of this module

    ..note: at the head of the file for readability.
    """
    parser = argparse.ArgumentParser(
            description='fetch a manga book from the web.'
            )

    parser.add_argument('config', type=argparse.FileType('r'),
                        help='the configuration file to use.')
    parser.add_argument('chapter', type=int,
                        help='the chapter to fetch.')

    parser.add_argument('-o', '--output', default='a.pdf', type=str,
                        help='the output file')
    parser.add_argument('-v', '--verbose', default=0, action="count",
                        help='How much verbose to be (none for minimal, '
                             '-v for info, -vv for debug')

    return parser


# type aliasing
URL = str


def url_ok(url: URL, session: requests.Session = requests.Session()) -> bool:
    """Check if a url exists

    :param url: The url to check.
    :param session: a requests session class for preformance.

    ..note: The defualt session is shared among **ALL** uses of this function,
            so, it is heighly recommanded to provied a uniqe session pre
            chapter.

    :return: True if OK, false otherwise.
    """
    r = session.head(url)
    return r.status_code == 200


def manga_fetcher(base_url: str,
                  startfrom: int = 0,
                  session: requests.Session = None) -> Iterator[URL]:
    """Check if the next page number exists

    :param base_url:  The base url format for fetching pages.
                      The format need to contain (in str.format syntax):
                        - page : the specific page to fetch.
    :param startfrom: The initial page to start the count from.
    :param session:   A requests session class, optional, yet is heighly
                      recommanded for perfomance.

    :return: The url of the next page to fetch (if exists)
    """
    index = startfrom  # type: int

    if session is None:
        session = requests.Session()  # type: requests.Session

    while url_ok(base_url.format(page=index), session):
        yield base_url.format(page=index)
        index += 1


def fetch_book(url: URL,
               get_format: str,
               destfile: str,
               chapter: int = 1) -> None:
    """Fetch a manga book from a collection of images online.

    :param url:        The url to fetch the manga from.
    :param get_format: The format of the url for fetching the book.
                       The format need to contain (in str.format syntax):
                            - url  : the url to fetch from.
                            - chapter : the chapter to fetch.
                            - page    : the specific page to fetch.
    :param chapter:    The chapter to fetch.
    :param destfile:   The name of the file to save the completed manga to.
    """
    logging.debug(f'{url=} {get_format=} {chapter=} {destfile=}')

    target = get_format.format(url=url, chapter=chapter, page='{page}')
    session = requests.Session()  # type: requests.Session

    for page in manga_fetcher(target, startfrom=1, session=session):
        logging.info(f'fetching {page}')


def main():
    parser = get_parser()
    args = parser.parse_args()

    log_format = '%(levelname)s: %(message)s'
    log_level = logging.WARNING

    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose > 1:
        log_format = '%(levelname)s: %(funcName)s: %(message)s'
        log_level = logging.DEBUG

    logging.basicConfig(format=log_format, level=log_level)
    logging.debug(f'recieved args = {args}')

    config = json.load(args.config)

    fetch_book(config['url'], config['format'], args.output, args.chapter)


if __name__ == '__main__':
    main()
