FROM python:3.8-slim-buster
RUN apt-get update && apt-get -y upgrade && apt-get clean
# copy the dependencies file to the working directory
COPY requirements.txt .
# install dependencies
RUN pip install -r requirements.txt
WORKDIR /app
# copy the content of the local src directory to the working directory
COPY server.py .
USER 65534
# command to run on container start
CMD [ "python", "./server.py" ]