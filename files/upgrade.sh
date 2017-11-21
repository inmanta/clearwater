#!/bin/bash
# clearwater pkg deps are not ok, so it often requires to run the script twice to finish.
# only make the second exec cause a failure.

/usr/bin/clearwater-upgrade -y
exec /usr/bin/clearwater-upgrade -y