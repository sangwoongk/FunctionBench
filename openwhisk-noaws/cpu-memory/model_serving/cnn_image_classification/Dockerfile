FROM openwhisk/action-python-v3.7:1.17.0

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip &&\
    pip3 install --no-cache-dir -r requirements.txt
    # ln -sf /usr/bin/python3 /usr/local/bin/python

# RUN apt-get update && apt-get upgrade -y 