#!/usr/bin/env sh
#
# Makefile for SublimeConfluence plugin 
# 
# @author <bprinty@gmail.com>
# ------------------------------------------------


# config
# ------
VERSION   = 0.0.1


# targets
# -------
all:
    @echo "usage: make [test|release]"


.PHONY: test
test:
	@echo "No tests yet ..."


release: test
	git tag -d $(TAG) || echo "local tag available"
	git push origin :$(TAG) || echo "remote tag available"
	git tag $(TAG) && git push origin $(TAG)
