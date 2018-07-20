FROM alpine:3.8

# Install packages
RUN apk --no-cache add gnupg haveged bash git rsync openssh

# Set the working directory
WORKDIR /upstream-update

# Copy the current directory contents into the container at our working directory
ADD . /upstream-update

RUN ln -s /upstream-update/bin/automerge.sh /usr/local/bin/automerge.sh

# Create an unpriviliged user
RUN adduser -D -u 1000 builder && \
    chown -R builder /usr/local && \
    chown -R builder /gnupg
USER builder
