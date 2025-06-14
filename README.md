# Guideline Ingest API

A minimal backend API that processes guideline documents through a two-step GPT chain: summarization and checklist generation.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd guideline-ingest-api
cp .env.example .env
# Edit .env with your OpenAI API key

# One-command bootstrap
docker compose up --build
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `POST /jobs/` - Submit guideline text, returns `event_id` in <200ms
- `GET /jobs/{event_id}/` - Get job status and results
- `GET /api/docs/` - Interactive OpenAPI documentation

## Architecture Decisions

**Django + DRF**: Chosen for rapid development with built-in ORM, admin interface, and excellent REST framework integration.

**Celery + Redis**: FIFO job queue with Redis as both broker and result backend. Simple, reliable, and scales well.

**PostgreSQL**: Robust database for production use with JSON field support for storing dynamic checklist data.

**Two-step GPT Chain**: 
1. GPT-3.5-turbo summarizes input text (max 500 tokens)
2. Second call generates JSON checklist from summary (max 800 tokens)

This approach reduces token usage while maintaining quality, as the checklist generation works on the condensed summary rather than full text.

## AI Tool Usage

Claude assisted with:
- Project structure and Django best practices
- Celery task design and error handling
- Test coverage including mocked OpenAI responses
- OpenAPI schema generation with drf-spectacular
- Docker containerization strategy

The AI helped establish clean separation of concerns, proper async task handling, and comprehensive test coverage (~75%).

## Testing

```bash
docker compose exec web python manage.py test
```

## License

MIT License