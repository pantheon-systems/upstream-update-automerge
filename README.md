# Upstream Update Build Docker Image

[![docker pull quay.io/getpantheon/upstream-update-build](https://img.shields.io/badge/image-quay-blue.svg)](https://quay.io/repository/getpantheon/upstream-update-build)

This is the source Dockerfile for the [getpantheon/upstream-update-build](https://quay.io/repository/getpantheon/upstream-update-build) docker image.

This docker image is used to build updates for Pantheon-maintained upstreams (drops-8 et. al.) from their respective upstreams.

## Usage
In CircleCI 2.0:
```
  docker:
    - image: quay.io/getpantheon/upstream-update-build:1.x
```
## Image Contents

- gnupg

## Test

python test.py
