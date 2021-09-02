from datajoint/djlab:py3.7-alpine as demo

user root
run apk add mesa-gl


user dja:anaconda
run \
    pip install imutils && \
    # chmod -R g+rwx,o+rwx /home/dja/.local/lib && \
    chmod -R g+w,o+w /home/dja/.cache && \
    conda install -yc conda-forge qt=5.12.5 opencv=4.2.0 && \
    find /opt/conda -user 3000 -exec chmod g+w "{}" \; && \
    conda clean -ya

# #Squashed Final Image
FROM scratch
COPY --from=demo / /
RUN chmod 4755 /startup && /startup -user=dja
LABEL maintainerName="Raphael Guzman" \
      maintainerEmail="raphael@vathes.com" \
      maintainerCompany="DataJoint"
USER dja:anaconda
ENV HOME /home/dja
ENV LANG C.UTF-8
ENV APK_REQUIREMENTS /tmp/apk_requirements.txt
ENV PIP_REQUIREMENTS /tmp/pip_requirements.txt
ENV CONDA_REQUIREMENTS /tmp/conda_requirements.txt
ENV DJLAB_CONFIG /tmp/djlab_config.yaml
ENV PATH "/home/dja/.local/bin:/opt/conda/bin:$PATH"
ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /home/dja
VOLUME /home/dja
VOLUME /tmp/.X11-unix
EXPOSE 8888
CMD ["jupyter", "lab"]