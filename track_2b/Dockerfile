FROM python:3.12-slim
WORKDIR /app
COPY src/ ./
ENV HOST=0.0.0.0 PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "judge_entry.py"]
