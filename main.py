#! /usr/bin/env python3
import argparse
import json
import logging
import requests

from PIL import Image
from pathlib import Path
from tempfile import TemporaryDirectory
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


def page_fetcher(base_url: str,
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


def download_file(url: URL,
                  output_dir: Path,
                  session: requests.Session) -> Path:
    """Download a file.

    :param url:        the url of the file to download.
    :param output_dir: the target directory to save the file to.
    :param session :   the request session.

    :return: The name of the downloaded file
    """
    local_filename = url.split('/')[-1]
    local_filename = output_dir / Path(local_filename)

    with session.get(url, stream=True) as stream:
        stream.raise_for_status()
        with open(local_filename, 'wb') as output:
            for chunk in stream.iter_content(chunk_size=2048):
                output.write(chunk)

    return local_filename


def fetch_book(url: URL,
               get_format: str,
               destfile: Path,
               chapter: int = 1) -> bool:
    """Fetch a manga book from a collection of images online.

    :param url:        The url to fetch the manga from.
    :param get_format: The format of the url for fetching the book.
                       The format need to contain (in str.format syntax):
                            - url  : the url to fetch from.
                            - chapter : the chapter to fetch.
                            - page    : the specific page to fetch.
    :param chapter:    The chapter to fetch.
    :param destfile:   The name of the file to save the completed manga to.

    :return: True if fetched the file, False otherwise.
    """
    logging.debug(f'{url=} {get_format=} {chapter=} {destfile=}')

    target = get_format.format(url=url, chapter=chapter, page='{page}')
    session = requests.Session()  # type: requests.Session

    if not url_ok(target.format(page=1)):
        logging.info('couldn\'t fetch the first page of {chapter = }')
        return False

    images = []  # type: list

    with TemporaryDirectory() as tmpdir:
        for page in page_fetcher(target, startfrom=1, session=session):
            logging.info(f'downloading {page}')
            images.append(Image.open(download_file(page,
                                                   Path(tmpdir),
                                                   session))
                          .convert('RGB'))

    logging.info(f'saving images of chapter {chapter} to PDF ({destfile})')
    images[0].save(destfile, save_all=True, append_images=images[1:])

    return True


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
