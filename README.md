> If you have any additional questions or comments send a mail to: finance@sciencebasedtargets.org

# SBTi Temperature Alignment Tool — REST API

REST API for portfolio temperature scoring, coverage analysis, and what-if scenario modeling using the [SBTi Finance Tool](https://github.com/ScienceBasedTargets/SBTi-finance-tool) Python package.

## Quickstart

```bash
docker-compose up --build
```

API docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness check with version |
| GET | `/v1/data-providers` | List configured data providers |
| POST | `/v1/temperature/score` | Calculate portfolio temperature scores |
| POST | `/v1/coverage` | Calculate portfolio coverage |
| POST | `/v1/temperature/whatif` | Run what-if scenario analysis |
| POST | `/v1/upload/csv` | Upload CSV portfolio and score |
| POST | `/v1/upload/excel` | Upload Excel portfolio and score |
| POST | `/v1/upload/parse` | Parse Excel file to JSON |

## Structure

```
.
├── .github/workflows    # CI and Docker publish workflows
├── app/                 # FastAPI application
│   ├── main.py          # App entry point
│   ├── config.py        # Configuration loader
│   ├── config.json      # Data provider configuration
│   ├── dependencies.py  # Shared utilities
│   ├── routers/         # Endpoint definitions
│   ├── schemas/         # Request/response models
│   └── data/            # Sample data files
├── tests/               # Pytest test suite
├── Dockerfile           # Container image
└── docker-compose.yml   # Local deployment
```

## Configuration

Data providers are configured in `app/config.json`. Override the config path with the `SBTI_CONFIG_PATH` environment variable.

## Development

```bash
# Install dependencies
poetry install

# Run locally
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Lint
ruff check app/ tests/
```

## Docker

```bash
# Build and run
docker-compose up --build

# Or directly
docker build -t sbti-api .
docker run -p 8000:8000 sbti-api
```

The container runs as a non-root user with a built-in health check.

## Requirements

- Python >= 3.11
- [sbti-finance-tool](https://github.com/ScienceBasedTargets/SBTi-finance-tool) >= 1.2.5
