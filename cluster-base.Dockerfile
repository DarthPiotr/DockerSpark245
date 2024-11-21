ARG debian_buster_image_tag=8-jre-slim
FROM openjdk:${debian_buster_image_tag}

# -- Layer: OS + Python 3.7

ARG shared_workspace=/opt/workspace
ARG python_version=3.11.9
ARG spark_version=3.5.3
ARG jupyterlab_version=4.3.0

RUN mkdir -p ${shared_workspace} && \
    apt-get update -y && \
	apt install -y curl gcc git &&\ 
	apt install -y build-essential zlib1g-dev libncurses5-dev && \
	apt install -y libsqlite3-dev && \
	apt install -y libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget libjpeg-dev && \
    apt install -y libbz2-dev llvm libncursesw5-dev xz-utils tk-dev liblzma-dev && \
	curl -O https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tar.xz  && \
    tar -xf Python-${python_version}.tar.xz && cd Python-${python_version} && ./configure && make -j 8 &&\
    make install && \
    apt-get update && apt-get install -y procps && apt-get install -y vim && apt-get install -y net-tools && \
    apt-get install -y python3-pip && \
	pip3 install pypandoc && \
    pip3 install pyspark==${spark_version} jupyterlab==${jupyterlab_version} && \
	pip3 install wget && \
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install numpy pandas matplotlib ipykernel pyarrow torch==2.3.0 numpy deeplake torchvision kornia>=0.7.0 Pillow timm==0.9.8 tqdm onedrivedownloader ftfy regex pyyaml && \
    pip3 install googledrivedownloader==0.4 onedrivedownloader==1.1.3 pytest==7.4.2 quadprog setproctitle==1.3.2 wandb timm==0.9.8 scikit-learn decorator accelerate transformers bitsandbytes && \
    # pip3 install https://pypi.org/simple && \
    # pip3 install -git+https://github.com/openai/CLIP.git && \
    rm -rf /var/lib/apt/lists/* 

ENV SHARED_WORKSPACE=${shared_workspace}

# -- Runtime

VOLUME ${shared_workspace}
CMD ["bash"]
