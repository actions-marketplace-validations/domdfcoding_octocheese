# Test that the whole process works

# stdlib
import datetime
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

# 3rd party
import pypi_json
import pytest
from coincidence import with_fixed_datetime
from coincidence.regressions import AdvancedFileRegressionFixture, check_file_regression
from domdf_python_tools.paths import PathPlus
from github3 import GitHub

# this package
from octocheese import copy_pypi_2_github


@pytest.mark.usefixtures("module_cassette")
@pytest.mark.parametrize("pypi_name", [None, "sphinx-toolbox"])
def test_operation(github_client: GitHub, advanced_file_regression: AdvancedFileRegressionFixture, pypi_name: str):
	captured_out = StringIO()

	with redirect_stderr(captured_out):
		with redirect_stdout(captured_out):

			copy_pypi_2_github(
					github_client,
					"sphinx-toolbox",
					"sphinx-toolbox",
					pypi_name=pypi_name,
					self_promotion=True,
					)

	check_file_regression(captured_out.getvalue(), advanced_file_regression)


@pytest.mark.parametrize("max_tags", [1, 5, 10, 20])
@pytest.mark.usefixtures("cassette")
def test_operation_max_tags(
		github_client: GitHub,
		advanced_file_regression: AdvancedFileRegressionFixture,
		max_tags: int,
		):
	captured_out = StringIO()

	with redirect_stderr(captured_out):
		with redirect_stdout(captured_out):
			with with_fixed_datetime(datetime.datetime(2020, 1, 1)):

				copy_pypi_2_github(
						github_client,
						"sphinx-toolbox",
						"sphinx-toolbox",
						pypi_name="sphinx-toolbox",
						self_promotion=True,
						max_tags=max_tags,
						)

	check_file_regression(captured_out.getvalue(), advanced_file_regression)


@pytest.mark.usefixtures("cassette")
def test_operation_prerelease(
		github_client: GitHub,
		advanced_file_regression: AdvancedFileRegressionFixture,
		monkeypatch,
		):
	mock_response = PathPlus("tests/sphinx_toolbox_pypi_mock_response.json").load_json()
	monkeypatch.setattr(pypi_json.ProjectMetadata, "get_releases_with_digests", lambda self: mock_response)
	captured_out = StringIO()

	with redirect_stderr(captured_out):
		with redirect_stdout(captured_out):

			copy_pypi_2_github(
					github_client,
					"octocheese-demo",
					"domdfcoding",
					pypi_name="sphinx-toolbox",
					self_promotion=True,
					)

	check_file_regression(captured_out.getvalue(), advanced_file_regression)
