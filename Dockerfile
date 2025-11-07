# Simple Dockerfile for Flask dashboard
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true \
 && pip install --no-cache-dir flask plotly pandas numpy matplotlib seaborn

COPY . .

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=dashboard/app.py

EXPOSE 5000

CMD ["python", "dashboard/app.py"]


