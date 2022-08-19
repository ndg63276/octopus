#!/bin/bash

aws s3 sync . s3://smartathome.co.uk/octopus/ --exclude ".git*" --exclude "scripts/*" --exclude "images/*" --exclude "tariffs.json" --exclude "*~"
aws cloudfront create-invalidation --distribution-id E1M3QR4XNVBQ5H --paths "/octopus/*"

