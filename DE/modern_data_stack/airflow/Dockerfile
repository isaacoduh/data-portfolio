FROM apache/airflow:2.6.1-python3.9

USER root
RUN apt-get update && apt-get install -y \
    libpq-dev gcc build-essential \
    libssl-dev libffi-dev \
    libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libblas-dev liblapack-dev gfortran \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# COPY the entry point script and set the correct permissions
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER airflow

# COPY the requirements.txt and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install dbt-core dbt-postgres
RUN pip install --no-cache-dir -r /requirements.txt

# SEt environment variables
ENV AIRFLOW_HOME=/opt/airflow

ENTRYPOINT [ "/entrypoint.sh" ]