#!/bin/bash

aws s3 sync . s3://smartathome.co.uk/octopus/ --exclude ".git*" --exclude "scripts/*" --exclude "images/*" --exclude "tariffs.json"
