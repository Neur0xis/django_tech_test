FROM python:3.12-slim

WORKDIR /app

# Evita archivos pyc y asegura logs en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema y PostgreSQL client
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root
RUN useradd -m -u 1000 appuser

# Copiar código y dar permisos
COPY --chown=appuser:appuser . .

# Exponer puerto
EXPOSE 8000

# Cambiar a usuario no-root
USER appuser

# Script de inicio para ejecutar migraciones y luego el servidor
CMD python manage.py migrate && \
    daphne -b 0.0.0.0 -p 8000 app.asgi:application

