FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/waitlist-kit

ENV WAITLIST_DB_PATH=/data/waitlist-kit/waitlist.db
ENV BASE_URL=http://localhost:8505

EXPOSE 8505

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8505"]
