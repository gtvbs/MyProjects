FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# OpenShift arbitrary non-root UID compatibility
RUN chgrp -R 0 /app && chmod -R g=u /app

EXPOSE 8080
USER 1001

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
