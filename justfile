# anki-sync justfile

set shell := ["bash", "-cu"]

default:
    @just --list

# Run the project
run *args:
    uv run python -m anki_sync {{ args }}

# Run linter (ruff + mypy)
lint:
    uv run ruff check src/ tests/
    uv run mypy src/

# Format code
fmt:
    uv run ruff format src/ tests/
    uv run ruff check --fix src/ tests/

# Check formatting + linting (CI gate)
check:
    uv run ruff format --check src/ tests/
    uv run ruff check src/ tests/
    uv run mypy src/

# Run tests
test *args:
    uv run pytest {{ args }}

# Run tests with coverage
test-cov:
    uv run pytest --cov=src/ --cov-report=term-missing

# Clean build artifacts
clean:
    rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ .ruff_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
