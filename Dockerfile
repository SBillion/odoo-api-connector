FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install curl and uv
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org uv || \
    (apt-get update && apt-get install -y curl && \
     curl -LsSf https://astral.sh/uv/install.sh | sh && \
     mv /root/.cargo/bin/uv /usr/local/bin/uv)

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app

# Install dependencies
RUN uv sync --no-dev

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
