import argparse
import logging
import sys
from pathlib import Path

from .analysis import StreamStats
from .errors import CliConfigError, StreamStatsError
from .parser import expore
from .report import write_report


def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".csv":
        return "csv"
    if ext == ".jsonl":
        return "jsonl"
    raise CliConfigError(f"cannot detect format of {path}, use --format")


def main(argv=None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Анализ файлов событий"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    st_cmd = subparsers.add_parser("analyze", help="Проанализировать файлы")
    st_cmd.add_argument("inputs", nargs="+", type=Path, help="Путь к файлу")
    st_cmd.add_argument("--format", choices=["csv", "jsonl"],
                        help="Формат входных файлов")
    st_cmd.add_argument("--output", type=Path,
                        help="Куда записывать json-отчёт (по умолчанию stdout)")
    st_cmd.add_argument("--skip-invalid", action="store_true",
                        help="Просто ропускать некорректные строки вместо, или остонавливать?")

    args = parser.parse_args(argv)

    if args.command == "analyze":
        st = StreamStats()

        try:
            for path in args.inputs:
                if not path.is_file():
                    raise CliConfigError(f"input not found: {path}")
                fmt = args.format or detect_format(path)
                for event in expore(path, fmt, args.skip_invalid, st.skip):
                    st.add(event)
            write_report(st.rezume([str(p) for p in args.inputs]), args.output)

        except StreamStatsError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except (OSError, UnicodeDecodeError) as e:
            print(f"error: cannot read or write file: {e}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
