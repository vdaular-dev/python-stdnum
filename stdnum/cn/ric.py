# ric.py - functions for handling Chinese Resident Identity Card Number
#
# Copyright (C) 2014 Jiangge Zhang
# Copyright (C) 2025 Arthur de Jong
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

"""RIC No. (Chinese Resident Identity Card Number).

The RIC No. is the unique identifier for issued to China (PRC) residents.

The number consist of 18 digits in four sections. The first 6 digits refers to
the resident's location, followed by 8 digits representing the resident's birth
day in the form YYYY-MM-DD. The next 3 digits is the order code which is the
code used to disambiguate people with the same date of birth and address code.
Men are assigned to odd numbers, women assigned to even numbers. The final
digit is the checksum.

>>> validate('360426199101010071')
'360426199101010071'
"""

from __future__ import annotations

import datetime

from stdnum.exceptions import *
from stdnum.util import clean, isdigits


def compact(number: str) -> str:
    """Convert the number to the minimal representation. This strips the
    number of any valid separators and removes surrounding whitespace."""
    return clean(number).upper().strip()


def get_birth_date(number: str) -> datetime.date:
    """Split the date parts from the number and return the birth date.
    Note that in some cases it may return the registration date instead of
    the birth date and it may be a century off."""
    number = compact(number)
    year = int(number[6:10])
    month = int(number[10:12])
    day = int(number[12:14])
    try:
        return datetime.date(year, month, day)
    except ValueError:
        raise InvalidComponent()


def get_birth_place(number: str) -> dict[str, str]:
    """Use the number to look up the place of birth of the person."""
    from stdnum import numdb
    number = compact(number)
    results = numdb.get('cn/loc').info(number[:6])
    info = {k: v for part, props in results for k, v in props.items()}
    if not info:
        raise InvalidComponent()
    year = get_birth_date(number).year
    # check if any found county was assigned at the birth year
    for county in info['county'].split(','):
        if not county.startswith('['):
            return info
        startend, county = county[1:].split(']')
        start, end = startend.split('-')
        if start and year < int(start):
            continue
        if end and year > int(end):
            continue
        info['county'] = county
        return info
    # none of the found counties were valid when the number was assigned
    raise InvalidComponent()


def calc_check_digit(number: str) -> str:
    """Calculate the check digit. The number passed should have the check
    digit included."""
    checksum = (1 - 2 * int(number[:-1], 13)) % 11
    return 'X' if checksum == 10 else str(checksum)


def validate(number: str) -> str:
    """Check if the number is a valid RIC number. This checks the length,
    formatting and birth date and place."""
    number = compact(number)
    if len(number) != 18:
        raise InvalidLength()
    if not isdigits(number[:-1]):
        raise InvalidFormat()
    if number[-1] != calc_check_digit(number):
        raise InvalidChecksum()
    get_birth_date(number)
    get_birth_place(number)
    return number


def is_valid(number: str) -> bool:
    """Check if the number is a valid RIC number."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False


def format(number: str) -> str:
    """Reformat the number to the standard presentation format."""
    return compact(number)
