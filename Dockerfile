FROM python:3.9-slim

RUN pip install --upgrade pip
RUN pip install PyGithub
RUN pip install requests
RUN pip install pybase64

COPY entrypoint.sh /entrypoint.sh
COPY run_kritik.py /run_kritik.py

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

