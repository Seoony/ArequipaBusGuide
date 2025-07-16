# Base de Python
FROM python:3.12.3-slim

# Instalar dependencias del sistema necesarias para PostGIS y psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    gdal-bin \
    binutils \
    libproj-dev \
    proj-data \
    proj-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Variables necesarias para que pip encuentre GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Crear directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . /app

# Instalar dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exponer el puerto por defecto de gunicorn
EXPOSE 8080

# Comando de inicio (puedes cambiar wsgi.py según la estructura de tu proyecto)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "nombre_de_tu_proyecto.wsgi:application"]
