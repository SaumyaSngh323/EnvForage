# Contributing to EnvForge

First off, thank you for considering contributing to EnvForge! It's people like you that make this tool better for everyone.

Please read the [Code of Conduct](./CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

## Development Setup

1. **Fork & Clone** the repository.
2. **Start Database**: We use Docker Compose for the PostgreSQL database.
   ```bash
   docker-compose up -d
   ```
3. **Install Dependencies**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```
4. **Run Migrations & Seeds**:
   ```bash
   alembic upgrade head
   python -m app.services.seed_service
   ```

## Folder Structure

```
EnvForge/
├── backend/            # FastAPI backend (API, Compatibility Engine, Templates)
├── cli/                # envforge-agent standalone CLI
├── docs/               # Architecture, ADRs, Workflows, Specs
├── .github/            # CI workflows, Issue Templates
└── docker-compose.yml
```

## How to Add Profiles

To add a new ML environment profile (e.g., JAX, TensorRT):
1. Review the [PROFILE_SPEC.md](./docs/PROFILE_SPEC.md) for the required schema.
2. Add your profile to `backend/seeds/profiles.yaml`.
3. Run the seed service (`python -m app.services.seed_service`) to test it locally.
4. Update `docs/FEATURES.md`.

## How to Add Templates

If you need a new output script format (e.g., `Makefile`):
1. Create the template in `backend/app/templates/jinja/`.
2. Register it in `TEMPLATE_MAP` inside `backend/app/templates/engine.py`.
3. Write a rendering test in `backend/tests/unit/templates/`.

## How to Test Scripts

We require high test coverage because generated scripts affect real systems.
- Run backend tests: `pytest tests/`
- Run CLI agent tests: `cd ../cli && pytest tests/`
- **Rule**: If you add a new CUDA version to the compatibility matrix, you *must* add a test case for it in `test_resolver.py`.

See [TESTING.md](./docs/TESTING.md) for more details.

## Pull Request Guidelines

1. Ensure all tests pass.
2. Format your code with `black` and `ruff`.
3. Ensure type checking passes (`mypy app/`).
4. Update relevant documentation in the `docs/` folder.
5. Fill out the Pull Request template completely.

## Commit Style

We follow [Conventional Commits](https://www.conventionalcommits.org/).

Examples:
- `feat(api): add new profile endpoint`
- `fix(agent): handle missing WMI gracefully on Windows`
- `docs: update ROADMAP.md for phase 2`
- `test(core): add edge cases for CompatibilityResolver`

## Branching Strategy

- `main` is the primary development branch.
- Feature branches: `feat/your-feature-name`
- Bugfix branches: `fix/your-bug-name`

## Getting Help
If you need help, please open an issue with the `question` label, or check out [SUPPORT.md](./SUPPORT.md).
