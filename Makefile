
UIS := $(wildcard *.ui)
PYS := $(UIS:.ui=.py)

##$(warning $(UIS) $(PYS))

default: $(PYS)

%.py: %.ui
	#/cygdrive/c/Python27/Scripts/pyside-uic $^ > $@
	pyside-uic $^ > $@

