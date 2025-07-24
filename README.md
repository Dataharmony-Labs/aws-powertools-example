# Powertools Example

## Setup

Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create virtual environment and install dependencies:
```bash
uv venv
uv sync
```

## Run

Run tests:
```bash
python -m unittest main.TestApiEndpoints
```