# tests/test_models.py
import pytest
from src.errors import InvalidEventError, InvalidTimestampError
from src.models import Markdown
from src.__main__ import main
import json

HEAD = "timestamp,level,source,message\n"
ROW_OK = "2024-05-01T12:00:00Z,INFO,api,ok\n"
JSON_OK = '{"timestamp":"2024-05-01T12:00:00Z","level":"INFO","source":"api","message":"ok"}\n'


@pytest.fixture
def make(tmp_path):
    """make('a.csv', 'текст') создаёт файл во временной папке и возвращает путь."""
    def _make(name, text="", encoding="utf-8"):
        p = tmp_path / name
        p.write_text(text, encoding=encoding)
        return p
    return _make

BASE = {"timestamp": "2024-05-01T12:00:00Z", "level": "INFO", "source": "api", "message": "ok"}




def test_ok():
    e = Markdown(BASE)
    assert e.level == "INFO"
    assert e.timestamp.tzinfo is not None


def test_naive_becomes_utc():
    e = Markdown({**BASE, "timestamp": "2024-05-01T12:00:00"})
    assert e.timestamp.tzinfo is not None


def test_empty_message_allowed():
    assert Markdown({**BASE, "message": ""}).message == ""


@pytest.mark.parametrize("patch, exc", [
    ({"timestamp": "вчера"}, InvalidTimestampError),
    ({"timestamp": 12345}, InvalidTimestampError),
    ({"level": "FATAL"}, InvalidEventError),
    ({"level": 5}, InvalidEventError),
    ({"source": "   "}, InvalidEventError),
    ({"source": None}, InvalidEventError),
    ({"message": 123}, InvalidEventError),
])
def test_invalid(patch, exc):
    with pytest.raises(exc):
        Markdown({**BASE, **patch})





def test_main_ok_stdout(make, capsys):
    p = make("a.csv", HEAD + ROW_OK)
    assert main(["analyze", str(p)]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 1


def test_main_strict_error(make, capsys):
    p = make("a.csv", HEAD + "2024-05-01T12:00:00Z,FATAL,db,x\n")
    assert main(["analyze", str(p)]) == 2
    assert "a.csv:2" in capsys.readouterr().err


def test_main_skip(make, tmp_path):
    p = make("a.csv", HEAD + "2024-05-01T12:00:00Z,FATAL,db,x\n" + ROW_OK)
    out = tmp_path / "r.json"
    assert main(["analyze", str(p), "--skip-invalid", "--output", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["skipped_invalid"] == 1


def test_main_unknown_extension(make, capsys):
    assert main(["analyze", str(make("a.txt", "x"))]) == 2


def test_main_missing_file(tmp_path):
    assert main(["analyze", str(tmp_path / "nope.csv")]) == 2


def test_main_not_utf8(tmp_path, capsys):
    p = tmp_path / "a.csv"
    p.write_bytes(HEAD.encode() + "2024-05-01T12:00:00Z,INFO,api,привет\n".encode("cp1251"))
    assert main(["analyze", str(p)]) == 2           # ветка UnicodeDecodeError


def test_main_output_dir_missing(make, tmp_path):
    p = make("a.csv", HEAD + ROW_OK)
    assert main(["analyze", str(p), "--output", str(tmp_path / "no_dir" / "r.json")]) == 2