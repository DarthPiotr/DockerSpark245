FROM cluster-base

# -- Layer: JupyterLab

ARG spark_version=3.5.3
ARG jupyterlab_version=4.3.0

RUN apt-get update -y && \
    # apt-get install -y python3-pip && \
	# pip3 install pypandoc && \
    # pip3 install pyspark==${spark_version} jupyterlab==${jupyterlab_version} && \
	# pip3 install wget && \
    # pip3 install numpy pandas matplotlib ipykernel pyarrow torch==2.5.0 numpy torchvision kornia>=0.7.0 Pillow timm==0.9.8 tqdm onedrivedownloader ftfy regex pyyaml && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/local/bin/python3 /usr/bin/python

# -- Runtime

EXPOSE 8888
WORKDIR ${SHARED_WORKSPACE}
CMD jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=

