from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}


def add_months(d: date, months: int) -> date:
    raw_month = d.month - 1 + months
    year = d.year + raw_month // 12
    month = raw_month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


def normalize(s: str) -> str:
    s = s.lower().strip()
    s = s.replace(".", "")
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s


def parse_absolute_date(s: str) -> date | None:
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if match:
        numeric_year, numeric_month, numeric_day = map(int, match.groups())
        return date(
            numeric_year,
            numeric_month,
            numeric_day,
        )

    match = re.fullmatch(r"([a-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)

    if match:
        month_name, month_day, month_year = match.groups()

        if month_name in MONTHS:
            return date(
                int(month_year),
                MONTHS[month_name],
                int(month_day),
            )

    match = re.fullmatch(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", s)

    if match:
        day_first_day, day_first_month, day_first_year = match.groups()

        if day_first_month in MONTHS:
            return date(
                int(day_first_year),
                MONTHS[day_first_month],
                int(day_first_day),
            )

    return None


def parse_relative_weekday(s: str, today: date) -> date | None:
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
        return today + timedelta(days=delta or 7)

    delta = (current - target) % 7
    return today - timedelta(days=delta or 7)


def add_unit(d: date, amount: int, unit: str) -> date:
    if unit.startswith("day"):
        return d + timedelta(days=amount)
    if unit.startswith("week"):
        return d + timedelta(weeks=amount)
    if unit.startswith("month"):
        return add_months(d, amount)
    if unit.startswith("year"):
        return add_years(d, amount)
    raise ValueError(f"Unsupported unit: {unit}")


def parse_offset_expression(s: str, today: date) -> date | None:
    amount_pattern = (
        r"(\d+|a|an|one|two|three|four|five|six|seven|eight|"
        r"nine|ten|eleven|twelve)"
    )
    unit_pattern = r"(day|days|week|weeks|month|months|year|years)"

    match = re.fullmatch(rf"in {amount_pattern} {unit_pattern}", s)
    if match:
        amount_text, unit = match.groups()
        return add_unit(today, parse_amount(amount_text), unit)

    match = re.fullmatch(rf"{amount_pattern} {unit_pattern} ago", s)
    if match:
        amount_text, unit = match.groups()
        return add_unit(today, -parse_amount(amount_text), unit)

    match = re.fullmatch(rf"{amount_pattern} {unit_pattern} from now", s)
    if match:
        amount_text, unit = match.groups()
        return add_unit(today, parse_amount(amount_text), unit)

    match = re.fullmatch(
        rf"{amount_pattern} {unit_pattern} (before|after) (.+)",
        s,
    )
    if match:
        amount_text, unit, direction, target_text = match.groups()
        target_date = parse(target_text, today)
        amount = parse_amount(amount_text)
        if direction == "before":
            amount = -amount
        return add_unit(target_date, amount, unit)

    match = re.fullmatch(
        rf"{amount_pattern} year[s]?(?: and|,)? {amount_pattern} month[s]? (before|after) (.+)",
        s,
    )
    if match:
        years_text, months_text, direction, target_text = match.groups()
        sign = -1 if direction == "before" else 1
        target_date = parse(target_text, today)
        result = add_years(target_date, sign * parse_amount(years_text))
        return add_months(result, sign * parse_amount(months_text))

    return None


def parse(s: str, today: date | None = None) -> date:
    if today is None:
        today = date.today()

    s = normalize(s)

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


def parse_amount(amount_text: str) -> int:
    number_words = {
        "a": 1,
        "an": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
    }

    if amount_text.isdigit():
        return int(amount_text)

    return number_words[amount_text]
