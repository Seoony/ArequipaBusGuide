FROM osgeo/gdal:ubuntu-full-3.8.4

# Instala dependencias de sistema
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-dev python3-pip \
    libpq-dev build-essential

# Establece python 3.12 como predeterminado
RUN ln -s /usr/bin/python3.12 /usr/local/bin/python && \
    python -m pip install --upgrade pip

# Establece el directorio de trabajo
WORKDIR /app

# Copia dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la app
COPY . .

# Expone el puerto
EXPOSE 8080

# Ejecuta el servidor de Django (usa gunicorn en producción)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "tu_proyecto.wsgi:application"]
