FROM python
WORKDIR /BOT
COPY . .
RUN pip3 install -r requirements.txt