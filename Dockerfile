FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV GDAL_VERSION=3.8.4
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:ubuntugis/ubuntugis-unstable && \
    apt-get update && apt-get install -y \
    gdal-bin libgdal-dev \
    python3.12 python3.12-dev python3-pip \
    libpq-dev postgresql-client \
    build-essential

# For pip GDAL compatibility with system-installed GDAL
RUN ln -s /usr/bin/python3.12 /usr/local/bin/python && \
    python -m pip install --upgrade pip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "tu_proyecto.wsgi:application"]
