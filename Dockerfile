FROM python:3.11
WORKDIR /bp_notify_bot
COPY requirements.txt /bp_notify_bot/
RUN pip install -r requirements.txt
COPY . /bp_notify_bot
CMD python -m bp_notify_bot