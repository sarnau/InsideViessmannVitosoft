#!/bin/bash

CMDPATH="`dirname \"$0\"`"
cd "$CMDPATH" || exit 1

dot graph.gv -Tpdf -O
open graph.gv.pdf
