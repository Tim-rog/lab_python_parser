import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from src.models import Markdown


@dataclass
class StreamStats:
    """Накопитель"""

    sum: int = 0
    by_lvl: Counter[str] = field(default_factory=Counter)
    by_src: Counter[str] = field(default_factory=Counter)
    error_src: Counter[str] = field(default_factory=Counter)
    start_dttm: datetime | None = None
    end_dttm: datetime | None = None
    shift: int = 0

    def add(self, event: Markdown)->None:
        """Запись подходит"""
        self.sum += 1
        self.by_lvl[event.level] += 1
        self.by_src[event.source] += 1

        if self.start_dttm:
            self.start_dttm = min(self.start_dttm, event.timestamp)
        else:
            self.start_dttm = event.timestamp

        if self.end_dttm:
            self.end_dttm = max(self.end_dttm, event.timestamp)
        else:
            self.end_dttm = event.timestamp

        if event.level == 'ERROR' or event.level == 'CRITICAL':
            self.error_src[event.source] += 1

    def skip(self)->None:
        """Прпоуск"""
        self.shift += 1

    def rezume(self, files: list) -> dict:
        items = sorted(self.error_src.items(), key=lambda kv: (-kv[1], kv[0]))
        top_er = [{"source": s, "count": c} for s, c in items[:5]]
        return {
            "files": files,
            "total": self.sum,
            "by_level": dict(self.by_lvl),
            "by_source": dict(self.by_src),
            "top_error_sources": top_er,
            "first_timestamp": self.start_dttm.isoformat() if self.start_dttm else None,
            "last_timestamp": self.end_dttm.isoformat() if self.end_dttm else None,
            "skipped_invalid": self.shift,
        }