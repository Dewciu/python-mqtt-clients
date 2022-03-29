FROM python:3.8

WORKDIR /first_task_v2

ENV VIRTUAL_ENV=/opt/venv 
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# COPY setup.py .
# RUN python3 setup.py install



CMD ["python3", "first_task/mqtt_clients.py"]