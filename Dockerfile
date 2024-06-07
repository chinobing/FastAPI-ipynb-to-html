# pull official base image
FROM ghcr.io/quarto-dev/quarto

# set work directory
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y python3-pip

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
