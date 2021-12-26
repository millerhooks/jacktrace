ARG BASE_CONTAINER=nvidia/cuda
ARG CUDA_VERSION=11.5.0
ARG RAPIDS_VERSION=latest
ARG RAPIDS_NAMESPACE=anon
ARG LINUX_VERSION=ubuntu18.04
ARG CUDA_SHORT_VERSION=${CUDA_VERSION}
FROM ${BASE_CONTAINER}:${CUDA_VERSION}-devel-${LINUX_VERSION}

ARG USE_FISH_SHELL
ARG CUDA_SHORT_VERSION

ENV DEBIAN_FRONTEND=noninteractive

RUN echo 'Acquire::HTTP::Proxy "http://172.17.0.1:3142";' >> /etc/apt/apt.conf.d/01proxy \
 && echo 'Acquire::HTTPS::Proxy "false";' >> /etc/apt/apt.conf.d/01proxy \
 && apt update \
 && apt install --no-install-recommends -y \
    pkg-config apt-utils apt-transport-https software-properties-common ca-certificates \
 && add-apt-repository -y ppa:git-core/ppa \
 # Needed to install compatible gcc 9/10 toolchains
 && add-apt-repository -y ppa:ubuntu-toolchain-r/test \
 # CUDA toolkit version usable to install `cuda-nsight-compute` and `cuda-nsight-systems` packages
 && NSIGHT_CUDA_VERSION=$(nvcc --version | head -n4 | tail -n1 | cut -d' ' -f5 | cut -d',' -f1 | sed "s/\./-/g") \
 && bash -c '\
if [[ "$USE_FISH_SHELL" == "YES" ]]; then \
    add-apt-repository -y ppa:fish-shell/release-3; \
fi' \
 && apt update \
 && apt install --no-install-recommends -y \
    jq ed git vim nano sudo curl wget entr less \
    # CMake dependencies
    curl libssl-dev libcurl4-openssl-dev zlib1g-dev \
    # Need tzdata for the pyarrow<->ORC tests
    tzdata \
    graphviz \
    gcc-9 g++-9 \
    gcc-10 g++-10 \
    ninja-build \
    build-essential \
    python3 python3-pip \
    # for building cudf-java
    maven openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre openjdk-8-jre-headless \
    # Install nsight-compute and nsight-systems
    nsight-compute-2021.3.0 \
    nsight-systems-2021.3.3 \
    # Not sure what this is but it seems important
    cuda-nsight-compute-${NSIGHT_CUDA_VERSION} \
    # This provides the `nsight-sys` GUI
    cuda-nsight-systems-${NSIGHT_CUDA_VERSION} \
    # Needed by `nsight-sys` GUI
    qt5-default libglvnd-dev libgl1-mesa-dev libegl1-mesa-dev libgles2-mesa-dev \
    libglib2.0-0 \
    libsqlite3-0 \
    xcb \
    xkb-data \
    openssh-client \
    dbus \
    fontconfig \
    gnupg \
    libfreetype6 \
    libx11-xcb1 \
    libxcb-glx0 \
    libxcb-xkb1 \
    libxcomposite1 \
    libxi6 \
    libxml2 \
    libxrender1 \
    libnuma1 \
    libnuma-dev \
 && bash -c '\
if [[ "$USE_FISH_SHELL" == "YES" ]]; then \
    apt install --no-install-recommends -y fish; \
fi' \
 && apt autoremove -y \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ARG GCC_VERSION=9
ENV GCC_VERSION=${GCC_VERSION}
ENV CXX_VERSION=${GCC_VERSION}

# Remove any existing gcc and g++ alternatives
RUN update-alternatives --remove-all cc  >/dev/null 2>&1 || true \
 && update-alternatives --remove-all c++ >/dev/null 2>&1 || true \
 && update-alternatives --remove-all gcc >/dev/null 2>&1 || true \
 && update-alternatives --remove-all g++ >/dev/null 2>&1 || true \
 && update-alternatives --remove-all gcov >/dev/null 2>&1 || true \
 # Install alternatives for gcc/g++/cc/c++/gcov
 && for x in 9 10; do \
    update-alternatives \
    --install /usr/bin/gcc gcc /usr/bin/gcc-${x} ${x}0 \
    --slave /usr/bin/cc cc /usr/bin/gcc-${x} \
    --slave /usr/bin/g++ g++ /usr/bin/g++-${x} \
    --slave /usr/bin/c++ c++ /usr/bin/g++-${x} \
    --slave /usr/bin/gcov gcov /usr/bin/gcov-${x}; \
 done \
 # Set gcc-${GCC_VERSION} as the default gcc
 && update-alternatives --set gcc /usr/bin/gcc-${GCC_VERSION}

ARG UID=1000
ARG GID=1000
ENV _UID=${UID}
ENV _GID=${GID}
ARG GOSU_VERSION=1.11
ARG TINI_VERSION=v0.18.0
ARG CMAKE_VERSION=3.21.3
ENV CMAKE_VERSION=${CMAKE_VERSION}

ARG PYTHON_VERSION=3.7
ENV PYTHON_VERSION="$PYTHON_VERSION"
ENV CUDA_SHORT_VERSION="$CUDA_SHORT_VERSION"
ENV CC="/usr/bin/gcc"
ENV CXX="/usr/bin/g++"

ARG PARALLEL_LEVEL=4
ENV PARALLEL_LEVEL=${PARALLEL_LEVEL}

# Install CMake
RUN mkdir -p /tmp/cmake \
 && curl -fsSL --compressed -o "/tmp/cmake-$CMAKE_VERSION-linux-$(uname -m).sh" \
    "https://github.com/Kitware/CMake/releases/download/v$CMAKE_VERSION/cmake-$CMAKE_VERSION-linux-$(uname -m).sh" \
 && sh "/tmp/cmake-$CMAKE_VERSION-linux-$(uname -m).sh" --skip-license --exclude-subdir --prefix=/tmp/cmake \
 && PATH="$PATH:/tmp/cmake/bin" \
 # Install ccache
 && git clone https://github.com/ccache/ccache.git /tmp/ccache && cd /tmp/ccache \
 && git checkout -b rapids-compose-tmp e071bcfd37dfb02b4f1fa4b45fff8feb10d1cbd2 \
 && mkdir -p /tmp/ccache/build && cd /tmp/ccache/build \
 && cmake \
    -DENABLE_TESTING=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DUSE_LIBB2_FROM_INTERNET=ON \
    -DUSE_LIBZSTD_FROM_INTERNET=ON .. \
 && make ccache -j${PARALLEL_LEVEL} && make install -j$PARALLEL_LEVEL && cd / && rm -rf /tmp/ccache \
 # Uninstall CMake
 && rm -rf /tmp/* \
 # Install tini
 && curl -s -L https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini -o /usr/bin/tini && chmod +x /usr/bin/tini \
 # Add gosu so we can run our apps as a non-root user
 # https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
 && curl -s -L https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64 -o /usr/local/sbin/gosu && chmod +x /usr/local/sbin/gosu

