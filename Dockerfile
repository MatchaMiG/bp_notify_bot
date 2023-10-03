FROM python:3.11
WORKDIR /bp_raid_notify
COPY requirements.txt /bp_raid_notify/
RUN pip install -r requirements.txt
COPY . /bp_raid_notify
CMD python -m bp_raid_notify