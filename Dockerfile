FROM python
ARG TOKEN_ARG
WORKDIR /BOT
COPY . .
ENV TOKEN=$TOKEN_ARG
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python", "./main.py"]