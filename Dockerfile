FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/
COPY entrypoint.sh entrypoint.sh

CMD ["./entrypoint.sh"]
