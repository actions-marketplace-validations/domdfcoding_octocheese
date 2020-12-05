#!/usr/bin/env python3
#
#  core.py
"""
The main logic of octocheese.
"""
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

# stdlib
import os
import pathlib
import re
import tempfile
import urllib.parse
from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Union

# 3rd party
import github
import github.GitRelease
import github.Repository
import requests
from domdf_python_tools.stringlist import StringList
from shippinglabel.pypi import get_pypi_releases

# this package
from octocheese.colours import error, success, warning

__all__ = ["update_github_release", "get_file_from_pypi", "copy_pypi_2_github", "make_release_message"]


def update_github_release(
		repo: github.Repository.Repository,
		tag_name: str,
		release_name: str,
		release_message: str,
		file_urls: Iterable[str] = ()
		) -> github.GitRelease.GitRelease:
	"""
	Update the given release on GitHub with the new name, message, and files.

	:param repo:
	:param tag_name:
	:param release_name:
	:param release_message:
	:param file_urls: The files to download from PyPI and add to the release.

	:return: The release, and a list of URLs for the current assets.

	.. versionchanged:: 0.3.0

		* Added the optional ``file_urls`` parameter.
		* Now returns only the :class:`github.GitRelease.GitRelease` object.
	"""

	current_assets = []

	try:
		release: github.GitRelease.GitRelease = repo.get_release(tag_name)

		# Check if and when last updated.
		m = re.match(".*<!-- Octocheese: Last Updated (.*) -->.*", release.body, re.DOTALL)

		if m:
			last_updated = datetime.strptime(m.group(1), "%Y-%m-%d")
			if last_updated < (datetime.now() - timedelta(days=7)):
				# Don't update release message if last touched more than 7 days ago.
				return release
			# elif last_updated < datetime(year=2020, month=12, day=6):
			# 	return release

		# Update existing release
		release.update_release(name=release_name, message=release_message)

		# Get list of current assets for release
		for asset in release.get_assets():
			current_assets.append(asset.name)

	except github.UnknownObjectException:
		# Create the release
		release = repo.create_git_release(tag=tag_name, name=release_name, message=release_message)

	if not file_urls:
		return release

	with tempfile.TemporaryDirectory() as tmpdir:

		for pypi_url in file_urls:
			filename = pathlib.PurePosixPath(urllib.parse.urlparse(pypi_url).path).name

			if filename in current_assets:
				warning(f"File '{filename}' already exists for release '{tag_name}'. Skipping.")
				continue

			if get_file_from_pypi(pypi_url, pathlib.Path(tmpdir)):
				success(f"Copying {filename} from PyPI to GitHub Releases.")
				release.upload_asset(os.path.join(tmpdir, filename))
			else:
				continue

	return release


def get_file_from_pypi(url: str, tmpdir: pathlib.Path) -> bool:
	"""
	Download the file with the given URL into the given (temporary) directory.

	:param url: The URL to download the file from.
	:param tmpdir: The (temporary) directory to store the downloaded file in.

	:return: Whether the file was downloaded successfully.
	"""

	filename = pathlib.PurePosixPath(urllib.parse.urlparse(url).path).name

	r = requests.get(url)
	if r.status_code != 200:  # pragma: no cover
		error(f"Unable to download '{filename}' from PyPI. Skipping.")
		return False

	(tmpdir / filename).write_bytes(r.content)

	return True


def copy_pypi_2_github(
		g: github.Github,
		repo_name: str,
		github_username: str,
		*,
		changelog: str = '',
		pypi_name: Optional[str] = None,
		self_promotion=True,
		):
	"""
	The main function for ``OctoCheese``.

	:param g:
	:param repo_name: The name of the GitHub repository.
	:param github_username: The username of the GitHub account that owns the repository.
	:param changelog:
	:param pypi_name: The name of the project on PyPI.
	:default pypi_name: The value of ``repo_name``.
	:param self_promotion: Show information about OctoCheese at the bottom of the release message.

	.. versionchanged:: 0.1.0

		Added the ``self_promotion`` option.
	"""

	repo_name = str(repo_name)
	github_username = str(github_username)

	if not pypi_name:
		pypi_name = repo_name

	pypi_name = str(pypi_name)

	pypi_releases = get_pypi_releases(pypi_name)

	repo = g.get_repo(f"{github_username}/{repo_name}")

	for tag in repo.get_tags():
		version = tag.name.lstrip('v')
		if version not in pypi_releases:
			warning(f"No PyPI release found for tag '{tag.name}'. Skipping.")
			continue

		print(f"Processing release for {version}")

		update_github_release(
				repo=repo,
				tag_name=tag.name,
				release_name=f"Version {version}",
				release_message=make_release_message(pypi_name, version, changelog, self_promotion=self_promotion),
				file_urls=pypi_releases[version],
				)


def make_release_message(name: str, version: Union[str, float], changelog: str = '', self_promotion=True) -> str:
	"""
	Create a release message.

	:param name: The name of the software.
	:param version: The version number of the new release.
	:param changelog: Optional block of text detailing changes made since the previous release.
	:no-default changelog:
	:param self_promotion: Show information about OctoCheese at the bottom of the release message.

	:return: The release message.

	.. versionchanged:: 0.1.0

		Added the ``self_promotion`` option.
	"""

	buf = StringList()

	if changelog:
		buf.extend(("### Changelog", changelog))
		buf.blankline(ensure_single=True)

	buf.append(f"Automatically copied from [PyPI](https://pypi.org/project/{name}/{version}).")
	buf.blankline(ensure_single=True)

	if self_promotion:
		buf.append("---")
		buf.blankline(ensure_single=True)

		buf.append("Powered by OctoCheese\\")

		# if TODAY.month == 12:
		# 	buf.append(
		# 			" | ".join((
		# 					"[🎄 docs](https://octocheese.readthedocs.io)",
		# 					"[☃️ repo](https://github.com/domdfcoding/octocheese)",
		# 					"[🎅 issues](https://github.com/domdfcoding/octocheese/issues)",
		# 					"[🎁 marketplace](https://github.com/marketplace/octocheese)",
		# 					))
		# 			)
		# else:
		buf.append(
				" | ".join((
						"[📝 docs](https://octocheese.readthedocs.io)",
						"[:octocat: repo](https://github.com/domdfcoding/octocheese)",
						"[🙋 issues](https://github.com/domdfcoding/octocheese/issues)",
						"[🏪 marketplace](https://github.com/marketplace/octocheese)",
						))
				)

		buf.blankline(ensure_single=True)

	buf.append(f"<!-- Octocheese: Last Updated {today()} -->")
	buf.blankline(ensure_single=True)

	return '\n'.join(buf)


#: Under normal circumstances returns :meth:`datetime.date.today`.
TODAY: date = date.today()


def today() -> str:
	return TODAY.strftime("%Y-%m-%d")
