from datetime import date

from nldate import parse


def test_today() -> None:
    assert parse("today", today=date(2025, 1, 1)) == date(2025, 1, 1)


def test_tomorrow() -> None:
    assert parse("tomorrow", today=date(2025, 1, 1)) == date(2025, 1, 2)


def test_yesterday() -> None:
    assert parse("yesterday", today=date(2025, 1, 1)) == date(2024, 12, 31)


def test_in_days() -> None:
    assert parse("in 5 days", today=date(2025, 1, 1)) == date(2025, 1, 6)


def test_days_from_now() -> None:
    assert parse("3 days from now", today=date(2025, 1, 1)) == date(
        2025,
        1,
        4,
    )


def test_next_tuesday() -> None:
    assert parse("next Tuesday", today=date(2025, 1, 1)) == date(
        2025,
        1,
        7,
    )


def test_last_friday() -> None:
    assert parse("last Friday", today=date(2025, 1, 8)) == date(
        2025,
        1,
        3,
    )


def test_absolute_date() -> None:
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_iso_date() -> None:
    assert parse("2025-12-01") == date(2025, 12, 1)


def test_before_expression() -> None:
    assert parse("5 days before December 1st, 2025") == date(
        2025,
        11,
        26,
    )


def test_after_expression() -> None:
    assert parse(
        "1 year and 2 months after January 1st, 2024",
    ) == date(2025, 3, 1)
