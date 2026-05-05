FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py jira_client.py objects.py test_runner.py branding.py ./
COPY .streamlit/config.toml .streamlit/config.toml
COPY test_cases/ test_cases/
COPY scripts/ scripts/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
