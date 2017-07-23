FROM jenkins
RUN apt-get update && apt-get install python-pip python-dev -y --fix-missing
RUN pip install virtualenv
