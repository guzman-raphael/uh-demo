FROM datajoint/djlab:py3.9-alpine
COPY --chown=anaconda:anaconda ./pip_requirements.txt /tmp/
RUN \
    /entrypoint.sh echo "Finished installing dependencies." && \
    rm /tmp/pip_requirements.txt
