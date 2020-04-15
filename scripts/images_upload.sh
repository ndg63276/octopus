#!/bin/bash

aws s3 cp "../images/" s3://smartathome.co.uk/octopus/images/ --recursive
