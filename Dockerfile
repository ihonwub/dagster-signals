# =============================================================================
# Image for the `signals` Dagster code location.
# -----------------------------------------------------------------------------
# THIS image is used in two places:
#   1. the long-lived gRPC code-server pod (serves the Definitions)
#   2. every short-lived RUN pod the K8sRunLauncher creates to execute a run
# Both need the same code + the same Dagster libraries, which is why one image
# serves both roles.
# =============================================================================
FROM python:3.11-slim

# Unbuffered stdout/stderr so logs stream to Kubernetes in real time.
ENV PYTHONUNBUFFERED=1

# Install Dagster + integrations (pinned in requirements.txt).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the team's Dagster project into the image.
WORKDIR /app
COPY signals_pipeline/ /app/signals_pipeline/

# Make the project importable as a top-level module from anywhere.
# The gRPC server runs `--python-module signals_pipeline.definitions`, so Python
# must be able to import `signals_pipeline` -- putting /app on PYTHONPATH does it.
ENV PYTHONPATH=/app

# Documentation only: the chart passes `--port 4001` to the gRPC server.
EXPOSE 4001
