FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
RUN useradd --create-home app && mkdir /data && chown app:app /data
USER app
ENV DEVDOCS_DB_PATH=/data/devdocs.sqlite3
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
