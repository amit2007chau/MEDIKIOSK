.PHONY: dev seed test backend-test frontend-build migrate rollback

dev:
	docker compose up --build

seed:
	docker compose exec backend python -m app.seed

test: backend-test frontend-build

backend-test:
	cd backend && python -m pytest -q

frontend-build:
	cd apps/patient-kiosk && npm run build
	cd apps/doctor-dashboard && npm run build
	cd apps/staff-dashboard && npm run build

migrate:
	cd backend && alembic upgrade head

rollback:
	cd backend && alembic downgrade -1

