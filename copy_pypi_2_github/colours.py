#!/usr/bin/env python3
#
#  colours.py
#
#  Copyright (c) 2020 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

# 3rd party
from domdf_python_tools.terminal_colours import Fore
from domdf_python_tools.utils import stderr_writer


def success(text) -> None:
	"""
	Prints the given text in green to stdout.

	:param text:
	:type text:
	"""

	print(Fore.GREEN(text))


def warning(text) -> None:
	"""
	Prints the given text in yellow to stderr.

	:param text:
	:type text:
	"""

	stderr_writer(Fore.YELLOW(text))


def error(text) -> None:
	"""
	Prints the given text in red to stderr.

	:param text:
	:type text:
	"""

	stderr_writer(Fore.RED(text))