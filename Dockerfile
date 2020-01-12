FROM arm32v6/alpine

RUN apk update && apk add python3
RUN python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip
RUN python3 -m pip install prometheus_client requests
COPY purpleair_exporter.py /root
EXPOSE 9564
ENTRYPOINT ["python3", "/root/purpleair_exporter.py"]