# tap-tableau-server

`tap-tableau-server` is a Singer tap for TableauServer.

Built with the Meltano [SDK](https://gitlab.com/meltano/singer-sdk) for Singer Taps.

## Installation

- [ ] `Developer TODO:` Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

```bash
pipx install tap-tableau-server
```

## Configuration

### Accepted Config Options

- [ ] `Developer TODO:` Provide a list of config options accepted by the tap.

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-tableau-server --about
```

### Source Authentication and Authorization

- [ ] `Developer TODO:` If your tap requires special access on the source system, or any special authentication requirements, provide those here.

## Usage

You can easily run `tap-tableau-server` by itself or in a pipeline using [Meltano](www.meltano.com).

### Executing the Tap Directly

```bash
tap-tableau-server --version
tap-tableau-server --help
tap-tableau-server --config CONFIG --discover > ./catalog.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.

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
