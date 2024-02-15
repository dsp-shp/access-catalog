FROM python:3.11-slim

WORKDIR /usr/src/app

RUN pip install --upgrade pip
RUN apt-get update && apt-get install -y g++ git cmake ninja-build libssl-dev
RUN pip install git+https://github.com/dsp-shp/services-access-catalog.git

RUN echo 'from catalog import run; run()' > main.py

CMD ["python", "main.py"]
