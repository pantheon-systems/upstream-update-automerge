FROM alpine:3.8

# Install packages
RUN apk --no-cache add gnupg haveged bash git rsync openssh

# Set the working directory
WORKDIR /gnupg

# Copy the current directory contents into the container at our working directory
ADD . /gnupg

# Create an unpriviliged user
RUN adduser -D -u 1000 builder && \
    chown -R builder /usr/local && \
    chown -R builder /gnupg
USER builder
