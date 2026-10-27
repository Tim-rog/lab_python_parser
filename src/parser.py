import csv
import json
import logging
from pathlib import Path

from .errors import InvalidEventError, UnsupportedFormatError
from .models import Markdown, fields

log = logging.getLogger(__name__)


def incorrect_l(err, path, lineno, skip_invalid, on_skip):
    """Плохая строка: в обычном режиме падаем, в skip-режиме пишем WARNING и считаем."""
    err.where = f"{path}:{lineno}"
    if not skip_invalid:
        raise err
    log.warning("skipping invalid row: %s", err)
    if on_skip:
        on_skip()


def csv_read(path: Path, skip_invalid=False, on_skip=None):
    """Читает csv почтрочно"""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            return

        missing = [n for n in fields if n not in reader.fieldnames]
        if missing:
            err = InvalidEventError(f"missing columns: {', '.join(missing)}")
            err.where = f"{path}:1"
            raise err

        for row in reader:
            try:
                event = Markdown(row)
            except InvalidEventError as err:
                incorrect_l(err, path, reader.line_num, skip_invalid, on_skip)
                continue
            yield event


def json_read(path: Path, skip_invalid=False, on_skip=None):
    """Читает json построчно"""
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise InvalidEventError("line is not a JSON object")
                event = Markdown(row)
            except json.JSONDecodeError as e:
                incorrect_l(InvalidEventError(f"invalid JSON: {e.msg}"),
                            path, lineno, skip_invalid, on_skip)
                continue
            except InvalidEventError as err:
                incorrect_l(err, path, lineno, skip_invalid, on_skip)
                continue
            yield event


reads = {"csv": csv_read, "jsonl": json_read}


def expore(path: Path, fmt: str, skip_invalid=False, on_skip=None):
    """Выбирает способ чтения по формату и возвращает генератор событий."""
    try:
        reader = reads[fmt]
    except KeyError:
        raise UnsupportedFormatError(f"unsupported format: {fmt!r}") from None
    return reader(path, skip_invalid, on_skip)
