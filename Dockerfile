FROM datajoint/djlab:py3.9-alpine
COPY --chown=anaconda:anaconda ./requirements.txt /tmp/
RUN \
    /entrypoint.sh echo "Finished installing dependencies." && \
    rm /tmp/requirements.txt
