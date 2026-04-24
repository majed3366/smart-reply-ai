migrate:
	python -m alembic -c db/alembic.ini upgrade head
