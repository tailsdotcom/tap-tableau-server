# tap-tableau-server

`tap-tableau-server` is a Singer tap for Tableau Server, focused (currently) on
extracting details _embedded inside Workbook files_. This includes
Datasources, Connections and Relations, as well as retrieving
table references from embedded Custom SQL text fields inside Relation entities.

Extracting the specifics of Datasources, Connections, Relations and Table References
from each Workbook help answer questions like:

- Which Workbooks depend on which tables in which databases?
- How many Workbooks depend on Excel, CSV or Google Sheets?
- Who's credentials are used for embedded connections, in which Workbooks?

Having answers to all of these questions has helped us with wrangling our
Tableau Server instance, which is several years old and has over 1000 Workbooks.

In future, we hope to extend this tap to cover other metadata that is exposed
by the Tableau Server API's directly (esp. Published Connections and child objects).
PR submission very welcome. Watch this space!

Built with the Meltano [SDK](https://gitlab.com/meltano/singer-sdk) for Singer Taps.

## Installation

```bash
pipx install tap-tableau-server
```

## Configuration

### Accepted Config Options

```
{
  "host": "<tableau server hostname>",
  "username": "<tableau server username>",
  "password": "<tableau server user password>",
  "limit": "<max number of workbooks to fetch per run>",
  "relation_types_exclude": ["<list of tableau workbook relation types to exclude>"],
  "relation_types_include": ["<list of tableau workbook relation types to include>"]
}
```

**Note:** The `limit` configuration is useful for large Tableau Server instances
where the number of workbooks to download may be in the 1000's. Setting a limit
on the number of workbooks retrieved per run effectively allows you to backfill
in fixed increments over several successive tap runs, reducing the load on your
server and minimising impact to other users.

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-tableau-server --about
```

### Source Authentication and Authorization

Only workbooks accessible to the user configured above can be extracted. Consider
creating a user with the broadest possible access to ensure you collect details
from all available Workbooks.

## Usage

You can easily run `tap-tableau-server` by itself or in a pipeline using [Meltano](www.meltano.com).

### Executing the Tap Directly

```bash
tap-tableau-server --version
tap-tableau-server --help
tap-tableau-server --config CONFIG --discover > ./catalog.json
```

## Developer Resources

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_tableau_server/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-tableau-server` CLI interface directly using `poetry run`:

```bash
poetry run tap-tableau-server --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-tableau-server
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-tableau-server --version
# OR run a test `elt` pipeline:
meltano elt tap-tableau-server target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://gitlab.com/meltano/singer-sdk/-/blob/main/docs/dev_guide.md) for more instructions on how to use the SDK to
develop your own taps and targets.
