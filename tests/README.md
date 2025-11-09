# Tests

Comprehensive test suite for the Ephemeral Audio Decay System.

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py

# Run specific test class
uv run pytest tests/test_api.py::TestStreamingEndpoint

# Run with coverage report
uv run pytest --cov=. --cov-report=html
```

## Test Structure

### `test_api.py`
Tests for Flask API endpoints:
- Health check endpoint
- Track listing
- Statistics endpoint
- Audio streaming
- CORS headers

### `test_degradation.py`
Tests for degradation engine:
- Dropout rate calculation
- Sample dropout application
- Mono and stereo audio handling
- Edge cases (0%, 100% degradation)

### `test_metadata.py`
Tests for metadata management:
- Metadata initialization
- Play count tracking
- Degradation calculation
- Track listing

## Test Coverage

Current test coverage: **31 tests** covering:
- ✅ API endpoints
- ✅ Audio streaming and degradation
- ✅ Metadata management
- ✅ Segment locking (implicit in streaming tests)
- ✅ Error handling
- ✅ Edge cases

## Adding New Tests

When adding new features, add corresponding tests:

1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures for setup/teardown
4. Test both success and failure cases
5. Run tests before committing

## Continuous Integration

These tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    uv sync --extra dev
    uv run pytest -v
```
