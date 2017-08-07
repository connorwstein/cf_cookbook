FROM jenkins
USER root
RUN apt-get update && apt-get install python-pip python-dev libpq-dev vim postgresql postgresql-contrib -y --fix-missing
RUN pip install virtualenv
USER postgres
RUN /etc/init.d/postgresql start && psql --command "CREATE DATABASE testing"
USER root
