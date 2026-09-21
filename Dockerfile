FROM node:22-bookworm-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY backend ./backend
COPY --from=frontend-build /frontend/dist ./frontend_dist

ENV PYTHONUNBUFFERED=1

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
