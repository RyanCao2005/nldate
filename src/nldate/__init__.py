from __future__ import annotations

import re
from datetime import date, timedelta

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
MONTHS.update(
    {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
)
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1

    days_in_month = [
        31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]

    day = min(d.day, days_in_month[month - 1])

    return date(year, month, day)


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


def clean_date_string(s: str) -> str:
    s = s.lower().strip()

    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)

    return s


def parse_absolute_date(s: str) -> date | None:
    iso_match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if iso_match:
        iso_year, iso_month, iso_day = map(int, iso_match.groups())

        return date(iso_year, iso_month, iso_day)
    slash_match = re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)
    if slash_match:
        slash_year, slash_month, slash_day = map(
            int,
            slash_match.groups(),
        )

        return date(
            slash_year,
            slash_month,
            slash_day,
        )
    month_match = re.fullmatch(
        r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        s,
    )

    if month_match:
        month_name, day, year = month_match.groups()

        if month_name in MONTHS:
            return date(
                int(year),
                MONTHS[month_name],
                int(day),
            )

    return None


def parse_relative_weekday(
    s: str,
    today: date,
) -> date | None:
    match = re.fullmatch(r"(next|last)\s+([a-z]+)", s)

    if not match:
        return None

    direction, weekday_name = match.groups()

    if weekday_name not in WEEKDAYS:
        return None

    target = WEEKDAYS[weekday_name]

    current = today.weekday()

    if direction == "next":
        delta = (target - current) % 7

        if delta == 0:
            delta = 7

        return today + timedelta(days=delta)

    delta = (current - target) % 7

    if delta == 0:
        delta = 7

    return today - timedelta(days=delta)


def parse_offset_expression(
    s: str,
    today: date,
) -> date | None:
    match = re.fullmatch(r"in (\d+) days?", s)

    if match:
        days = int(match.group(1))

        return today + timedelta(days=days)

    match = re.fullmatch(r"(\d+) days? from now", s)

    if match:
        days = int(match.group(1))

        return today + timedelta(days=days)

    match = re.fullmatch(
        r"(\d+) days? before (.+)",
        s,
    )

    if match:
        num_days, target = match.groups()

        target_date = parse(target, today)

        return target_date - timedelta(days=int(num_days))

    match = re.fullmatch(
        r"(\d+) year[s]? and (\d+) month[s]? after (.+)",
        s,
    )

    if match:
        num_years, num_months, target = match.groups()

        target_date = parse(target, today)

        result = add_years(target_date, int(num_years))

        result = add_months(result, int(num_months))

        return result

    return None


def parse(
    s: str,
    today: date | None = None,
) -> date:
    if today is None:
        today = date.today()

    s = clean_date_string(s)

    if s == "today":
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    absolute = parse_absolute_date(s)

    if absolute is not None:
        return absolute

    weekday_result = parse_relative_weekday(s, today)

    if weekday_result is not None:
        return weekday_result

    offset_result = parse_offset_expression(s, today)

    if offset_result is not None:
        return offset_result

    raise ValueError(f"Could not parse date string: {s}")
