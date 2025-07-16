FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY pyproject.toml uv.lock .
RUN uv sync
COPY . .
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD ["uv", "run", "app.py"]