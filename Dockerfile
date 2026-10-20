FROM python:3.12-slim-bookworm
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
USER 1000:1000
ENTRYPOINT ["amazon-sync"]
CMD ["plan", "--config", "/config/collections.toml"]
