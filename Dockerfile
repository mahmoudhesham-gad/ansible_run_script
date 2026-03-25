## ------------------------------- Builder Stage ------------------------------ ##
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv /uv /bin/
WORKDIR /build
RUN uv venv --relocatable .venv \
  && uv pip install --python .venv/bin/python ansible-core \
  && .venv/bin/ansible-galaxy collection install \
  community.docker \
  community.general \
  && rm -rf /root/.ansible/tmp

## ------------------------------- Production Stage ------------------------------ ##
FROM python:3.14-slim AS production

RUN apt-get update \
  && apt-get install -y --no-install-recommends openssh-client sshpass \
  && rm -rf /var/lib/apt/lists/*

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

COPY --from=builder /build/.venv ${APP_HOME}/.venv
COPY --from=builder /root/.ansible/collections /root/.ansible/collections

ENV PATH="${APP_HOME}/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["ansible-playbook"]
