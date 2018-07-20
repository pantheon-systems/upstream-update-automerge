FROM alpine:3.8

# Install packages
RUN apk --no-cache add gnupg haveged

# Set the working directory
WORKDIR /gnupg

# Copy the current directory contents into the container at our working directory
ADD . /gnupg

# Create an unpriviliged user
RUN groupadd -g 999 builder && \
    useradd -r -m -u 999 -g builder builder && \
    chown -R builder /usr/local && \
    chown -R builder /gnupg
USER builder
